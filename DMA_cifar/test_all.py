import os
import sys
import torch
import copy
import numpy as np
import random
import time
import argparse
import torch.nn.functional as F
import torch.nn as nn
import torch.optim as optim
import pdb
import matplotlib.pyplot as plt
from torchvision.utils import save_image


from torch.utils.data import DataLoader
from attacks.cw_black import BlackBoxL2
from data import load_data
from PIL import Image
from learner import Learner
from attacks.generate_gradient import generate_gradient

from load_attacked_and_meta_model import load_attacked_model, load_meta_model
from utils import Logger,save_gradient
from options import args

#linda
from tensorboardX import SummaryWriter
writer=SummaryWriter('run')

os.environ['CUDA_VISIBLE_DEVICES'] = '0'



def main( device):
    use_log = not args.use_zvalue
    is_inception = args.dataset == "imagenet"
    
    # load data and network
    print('Loading %s model and test data' % args.dataset)
    _, test_loader = load_data(args)
    assert test_loader is not None
    
    model = load_attacked_model(args, 3, device)


    meta_model_path = args.load_ckpt
    assert os.path.exists(meta_model_path)
    print('Loading meta model from %s' % meta_model_path)
    meta_model = load_meta_model(args, meta_model_path, device)
    print('Done...')

    if args.attack == 'ours':
        generate_grad = generate_gradient(
                device,
                targeted = not args.untargeted,
                )
        attack = BlackBoxL2(
                targeted = not args.untargeted,
                max_steps = args.maxiter,
                search_steps = args.binary_steps,
                cuda = not args.no_cuda,
                )
    
    os.system("mkdir -p {}/{}".format(args.save, args.dataset))

    meta_optimizer = optim.Adam(meta_model.parameters(), lr = 0.01)

    img_no = 0
    total_success = 0
    l2_total = 0.0
    avg_step = 0
    avg_time = 0
    avg_qry = 0
    average_query=0

    # acc = save_gradient(model,device,test_loader,mode="test")
    model.eval()
    

    for i, (img, target) in enumerate(test_loader):
        print()
        print()
        print('start')
        img, target = img.to(device), target.to(device)
        pred_logit = model(img)
        
        print('Predicted logits', pred_logit.data[0], '\nProbability', F.softmax(pred_logit, dim = 1).data[0])
        pred_label = pred_logit.argmax(dim=1)
        print('The original label before attack', pred_label.item())
        if pred_label != target:
            print("Skip wrongly classified image no. %d, original class %d, classified as %d" % (i, pred_label.item(), target.item()))
            continue

        img_no += 1
        if img_no > args.total_number:
            break
        timestart = time.time()
        
        
        #######################################################################

        meta_model_copy = copy.deepcopy(meta_model)
    
        if not args.untargeted:
            if target ==9 :
                target = torch.tensor([0]).long().cuda()
            else:
                target = torch.tensor([1]).long().cuda() + target
            
 
        #######################################################################
        
        
        
        adv, const, first_step,query_bias,query_times_for_zoograd = attack.run(model, meta_model_copy, img, target, i)
        timeend = time.time()


        if len(adv.shape) == 3:
            adv = adv.reshape((1,) + adv.shape)
        adv = torch.from_numpy(adv).permute(0, 3, 1, 2).cuda()
        #print('adv min and max', torch.min(adv).item(), torch.max(adv).item(), '', torch.min(img).item(), torch.max(img).item())
        diff = (adv-img).cpu().numpy()
        l2_distortion = np.sum(diff**2)**.5

        #linda
        writer.add_scalar('baseline',l2_distortion,global_step=i)
        print('L2 distortion', l2_distortion)
        
        adv_pred_logit = model(adv)
        adv_pred_label = adv_pred_logit.argmax(dim = 1)
        print('The label after attack', adv_pred_label.item())
        
        success = False
        if args.untargeted:
            if adv_pred_label != target:
                success = True
        else:
            if adv_pred_label == target:
                success = True
        if l2_distortion > 20:
            success = False
        if success:
            total_success += 1
            l2_total += l2_distortion
            avg_step += first_step
            avg_time += timeend - timestart
            #only 1 query for i pixel, because the estimated function is f(x+h)-f(x)/h 
            avg_qry += (first_step-1)//args.finetune_interval*args.update_pixels*1+first_step
            average_query += query_times_for_zoograd*args.update_pixels+first_step

        print('end')

    

    if total_success == 0:
        pass
    else:              
        print("[STATS][L1] total = {}, seq = {}, time = {:.3f}, success = {}, distortion = {:.5f}, avg_step = {:.5f},avg_query = {:.5f}, new_query = {:.5f},success_rate = {:.3f}".format(img_no, i, avg_time / total_success, success, l2_total / total_success, avg_step / total_success,avg_qry / total_success, average_query / total_success,total_success / float(img_no)))

    sys.stdout.flush()
     
           

if __name__ == "__main__":
    USE_DEVICE = torch.cuda.is_available()
    device = torch.device('cuda' if USE_DEVICE else 'cpu')
    main( device)


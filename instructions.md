
## **Activate the environment and right path**
conda activate gpu
cd /home/projects/martin_wd/project

### **Training**
```
python train.py  \
    --root_dir /home/projects/martin_wd/ \
    --dataset_dir /home/projects/martin_wd/data/ \
    --model_name unet \
    --epochs 2 \
    --batch_size 3 \
    --experiment waterbody \
    --patchify True \
    --patch_size 256 \
    --patch_class_balance True
```

### **Testing**

```
python test.py \
    --dataset_dir home/projects/martin_wd/data \
    --model_name unet \
    --load_model_name unet_ex_cls_balance_epochs_2000_14-Mar-22.hdf5 \
    --plot_single False \
    --index -1 \
    --patchify True \
    --experiment waterbody_test 
```


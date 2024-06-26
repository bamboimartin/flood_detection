import os
import glob
import json
import rasterio
import pathlib
import numpy as np
import pandas as pd

from matplotlib.ticker import FormatStrFormatter
from utils import get_config_yaml, create_false_color_composite
from dataset import get_test_dataloader, read_img, transform_data
from tensorflow.keras.models import load_model
import earthpy.plot as ep
import earthpy.spatial as es
from matplotlib import pyplot as plt

def display_all(data):
    
    
    pathlib.Path((config['visualization_dir']+'display')).mkdir(parents = True, exist_ok = True)

    for i in range(len(data)):
        with rasterio.open((data.feature_ids.values[i]+"_vv.tif")) as vv:
            vv_img = vv.read(1)
        with rasterio.open((data.feature_ids.values[i]+"_vh.tif")) as vh:
            vh_img = vh.read(1)
        with rasterio.open((data.feature_ids.values[i]+"_nasadem.tif")) as dem:
            dem_img = dem.read(1)
        with rasterio.open((data.masks.values[i])) as l:
            lp_img = l.read(1)
            lp_img[lp_img==255]=0
        id = data.feature_ids.values[i].split("/")[-1]
        display_list = {
                     "vv":vv_img,
                     "vh":vh_img,
                     "dem":dem_img,
                     "label":lp_img}


        plt.figure(figsize=(12, 8))
        title = list(display_list.keys())

        for i in range(len(display_list)):
            plt.subplot(1, len(display_list), i+1)
            
            
            if title[i]=="dem":
                ax = plt.gca()
                hillshade = es.hillshade(display_list[title[i]], azimuth=180)
                ep.plot_bands(
                    display_list[title[i]],
                    cbar=False,
                    cmap="terrain",
                    title=title[i],
                    ax=ax
                )
                ax.imshow(hillshade, cmap="Greys", alpha=0.5)
            
            
            elif title[i]=="vv" or title[i]=="vh":
                plt.title(title[i])
                plt.imshow((display_list[title[i]]), cmap="gray")
                plt.axis('off')
            else:
                plt.title(title[i])
                plt.imshow((display_list[title[i]]))
                plt.axis('off')

        prediction_name = "img_id_{}.png".format(id) 
        plt.savefig(os.path.join((config['visualization_dir']+'display'), prediction_name), bbox_inches='tight', dpi=800)
        plt.clf()
        plt.cla()
        plt.close()


def class_balance_check(patchify, data_dir):
    
    if patchify:
        with open(data_dir, 'r') as j:
            train_data = json.loads(j.read())
        labels = train_data['masks']
        patch_idx = train_data['patch_idx']
    else:
        train_data = pd.read_csv(data_dir)
        labels = train_data.masks.values
        patch_idx = None
    class_one_t = 0
    class_zero = 0
    total = 0

    for i in range(len(labels)):
        with rasterio.open(labels[i]) as l:
            mask = l.read(1)
        mask[mask == 255] = 0
        if patchify:
            idx = patch_idx[i]
            mask = mask[idx[0]:idx[1], idx[2]:idx[3]]
        total_pix = mask.shape[0]*mask.shape[1]
        total += total_pix
        class_one = np.sum(mask)
        class_one_t += class_one
        class_zero_p = total_pix-class_one
        class_zero += class_zero_p
    
    print("Water Class percentage in train after class balance: {}".format((class_one_t/total)*100))

def class_distribution(data):
    masks = data["masks"]
    pixels = {"Water":0, "NON-Water":0}
    for i in range(len(masks)):
        mask = read_img(masks[i], label=True)
        pixels["Water"] += np.sum(mask)
        pixels["NON-Water"] += (mask.shape[0]*mask.shape[1]) - np.sum(mask)
    return pixels


def display_color_composite(data):
    
    
    pathlib.Path((config['visualization_dir']+'display_color_composite')).mkdir(parents = True, exist_ok = True)
    
    for i in range(len(data)):
        f, ax = plt.subplots(1, 2, figsize=(9, 9))
        with rasterio.open((data.feature_ids.values[i]+"_vv.tif")) as vv:
            vv_img = vv.read(1)
        with rasterio.open((data.feature_ids.values[i]+"_vh.tif")) as vh:
            vh_img = vh.read(1)
        with rasterio.open((data.feature_ids.values[i]+"_nasadem.tif")) as dem:
            dem_img = dem.read(1)
        with rasterio.open((data.masks.values[i])) as l:
            lp_img = l.read(1)
            lp_img[lp_img==255]=0

        
        s1_img = create_false_color_composite(vv_img, vh_img)

        
        ax[0].imshow(s1_img)
        ax[0].set_title("Feature", fontsize=14)

        
        label = np.ma.masked_where((lp_img == 0) | (lp_img == 255), lp_img)

        
        ax[1].imshow(s1_img)
        ax[1].imshow(label, cmap="cool", alpha=1)
        ax[1].set_title("Feature with Water Label", fontsize=14)
        id = data.feature_ids.values[i].split("/")[-1]
        prediction_name = "img_id_{}.png".format(id) 
        plt.savefig(os.path.join((config['visualization_dir']+'display_color_composite'), prediction_name), bbox_inches='tight', dpi=800)

def save_for_comparison(config):
    

    
    models_paths = ["/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/unet/*.hdf5",
                    "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/kuc_u2net/*.hdf5",
                    "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/dncnn/*.hdf5",
                    "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/kuc_attunet/*.hdf5",
                    "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/sm_fpn/*.hdf5",
                    "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/sm_linknet/*.hdf5",
                    "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/unet++/*.hdf5",
                    "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/vnet/*.hdf5",
                    ]

    
    models_paths = [x for path in models_paths for x in glob.glob(path)]

    mnet_paths = ["/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/mnet/mnet_ex_regular_epochs_2000_17-Mar-22.hdf5",
                  "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/mnet/mnet_ex_cls_balance_epochs_2000_17-Mar-22.hdf5",
                  "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/mnet/mnet_ex_patchify_WOC_256_epochs_2000_12-Apr-22.hdf5",
                  "/home/mdsamiul/github_project/flood_water_mapping_segmentation/model/mnet/mnet_ex_patchify_epochs_2000_02-Apr-22.hdf5"]

    models_paths = models_paths + mnet_paths

    
    
    indices = [15, 43, 27] 

    
    plot_tensors = {}
    for idx in indices:
        plot_tensors[idx] = {"regular":[],
                    "cls":[],
                    "p_woc":[],
                    "patchify":[]}

    
    cols = ["VV", "VH", "DEM", "GR", "UNET", "U2NET", "DNCNN", "ATTUNET","FPN","LINKNET","UNET++","VNET", "FAPNET"]

    
    cat_paths = {0:{"regular":[],
                    "cls":[],},
                1:{"p_woc":[],
                    "patchify":[]}}
    for path in models_paths:
        c1 = path.split("_")[6]
        c2 = path.split("_")[7]
        if c1 not in ["regular", "cls", "patchify"]:
            c1 = path.split("_")[8]
            c2 = path.split("_")[9]
        
        if c1 == "patchify" and c2 =="WOC":
            cat_paths[1]["p_woc"].append(path)
        elif c1 == "regular":
            cat_paths[0]["regular"].append(path)
        elif c1 == "cls":
            cat_paths[0]["cls"].append(path)
        else:
            cat_paths[1]["patchify"].append(path)


    
    with open(config['p_test_dir'], 'r') as j:
        patch_test_dir = json.loads(j.read())
        
    df = pd.DataFrame.from_dict(patch_test_dir)
    test_dir = pd.read_csv(config['test_dir'])

    
    config['patchify'] = True
    test_dataset = get_test_dataloader(config)

    
    for key in cat_paths[1].keys():
        
        
        for q, path in enumerate(cat_paths[1][key]):
            
            
            model = load_model(path, compile = False)
            
            
            for idx in indices:
                total_score = 0.0
                
                
                Pt_idx = df[df["masks"]==test_dir["masks"][idx]].index
                
                
                pred_full_label = np.zeros((512,512), dtype=int)
                
                
                for j in Pt_idx:
                    p_idx = patch_test_dir["patch_idx"][j]
                    feature, mask, _ = test_dataset.get_random_data(j)
                    pred_mask = model.predict(feature)
                    pred_mask = np.argmax(pred_mask, axis = 3)
                    
                    
                    pred_full_label[p_idx[0]:p_idx[1], p_idx[2]:p_idx[3]] = np.bitwise_or(pred_full_label[p_idx[0]:p_idx[1], p_idx[2]:p_idx[3]], pred_mask[0].astype(int))
                
                
                if q==0:
                    feature = read_img(test_dir["feature_ids"][idx], in_channels=config['in_channels'])
                    mask = transform_data(read_img(test_dir["masks"][idx], label=True), config['num_classes'])
                    plot_tensors[idx][key].append(feature[:,:,0])
                    plot_tensors[idx][key].append(feature[:,:,1])
                    plot_tensors[idx][key].append(feature[:,:,2])
                    plot_tensors[idx][key].append(np.argmax([mask], axis = 3)[0])
                
                
                plot_tensors[idx][key].append(pred_full_label)

    
    config['patchify'] = False
    test_dataset = get_test_dataloader(config)

    
    for key in cat_paths[0].keys():
        
        
        for q, path in enumerate(cat_paths[0][key]):
            
            
            model = load_model(path, compile = False)
            
            
            for idx in indices:
                feature, mask, _ = test_dataset.get_random_data(idx)
                prediction = model.predict_on_batch(feature)
                
                
                if q==0:
                    plot_tensors[idx][key].append(feature[0][:,:,0])
                    plot_tensors[idx][key].append(feature[0][:,:,1])
                    plot_tensors[idx][key].append(feature[0][:,:,2])
                    plot_tensors[idx][key].append(np.argmax(mask, axis = 3)[0])
                
                
                plot_tensors[idx][key].append(np.argmax(prediction, axis = 3)[0])

    
    fig = plt.figure(figsize=(12, 14))
    fig.subplots_adjust(hspace=0.3, wspace=0)
    gs = fig.add_gridspec(len(cols), len(indices)*4, hspace=0.0, wspace=0.0)
    ax = fig.subplots(nrows=len(cols), ncols=len(indices)*4, sharex='col', sharey='row')

    
    i = 0

    
    for key in indices:
        
        
        for k in plot_tensors[key].keys():
            
            
            for j in range(len(plot_tensors[key][k])):
                
                
                if j == 0 or j==1:
                    ax[j][i].imshow(plot_tensors[key][k][j], cmap='gray', vmin=np.min(plot_tensors[key][k][j]), vmax=np.max(plot_tensors[key][k][j]))
                    
                    
                    if j == 0:
                        if k=="regular":
                            ax[j][i].set_title("CFR", fontsize=10, fontweight="bold")
                        elif k=="cls":
                            ax[j][i].set_title("CFR-CB", fontsize=10, fontweight="bold")
                        elif k=="patchify":
                            ax[j][i].set_title("PHR-CB", fontsize=10, fontweight="bold")
                        else:
                            ax[j][i].set_title("PHR", fontsize=10, fontweight="bold")
                    
                    
                    ax[j][i].xaxis.set_major_locator(plt.NullLocator())
                    ax[j][i].yaxis.set_major_locator(plt.NullLocator())
                
                
                elif j == 2:
                    hillshade = es.hillshade(plot_tensors[key][k][j], altitude=10)
                    ep.plot_bands(
                        plot_tensors[key][k][j],
                        ax=ax[j][i],
                        cmap="terrain",
                        cbar=False
                    )
                    ax[j][i].imshow(hillshade, cmap="Greys", alpha=0.5)
                    
                    
                    ax[j][i].xaxis.set_major_locator(plt.NullLocator())
                    ax[j][i].yaxis.set_major_locator(plt.NullLocator())
                
                
                else:
                    ax[j][i].imshow(plot_tensors[key][k][j])
                    
                    
                    ax[j][i].xaxis.set_major_locator(plt.NullLocator())
                    ax[j][i].yaxis.set_major_locator(plt.NullLocator())
            i += 1

    
    plt.subplots_adjust(hspace=0, wspace=0)

    
    for i in range(len(ax)):
        ax[i][0].set_ylabel(cols[i], fontsize=10, rotation=0, fontweight="bold")
        ax[i][0].yaxis.set_label_coords(-0.5, 0.4)

    
    plt.savefig((config['visualization_dir']+"worst4.png"), bbox_inches='tight', dpi=1200, transparent=True)
    plt.show()
    

def meaniou_plot(config):
    def meaniou(data, ax, model):
        df = pd.DataFrame(data).T
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        df = df.join(pd.DataFrame(model, index=["id"]).T)
        x_values = df.iloc[:, 0:-1]
        y = df.iloc[:, -1]

        for col in x_values.columns:
            
            ax.plot(y, x_values[col], linewidth=3.0, marker='o', markersize=10)
        
        labels = ax.get_xticklabels() + ax.get_yticklabels()
        for label in labels:
            label.set_fontweight('bold')
        plt.xticks(ticks=y, labels=data.keys())


    val = {"UNET": {"CFR":0.8467, "CFR-CB": 0.8563, "PHR": 0.8590, "PHR-CB": 0.8717},
            "VNET": {"CFR":0.8451, "CFR-CB": 0.8463, "PHR": 0.8254, "PHR-CB": 0.8545},
            "DNCNN": {"CFR":0.8637, "CFR-CB": 0.8702, "PHR": 0.8552, "PHR-CB": 0.8855},
            "UNET++": {"CFR":0.8557, "CFR-CB": 0.8556, "PHR": 0.8597, "PHR-CB": 0.8867},
            "U2NET": {"CFR":0.8500, "CFR-CB": 0.8564, "PHR": 0.8719, "PHR-CB": 0.8639},
            "ATTUNET": {"CFR":0.8545, "CFR-CB": 0.8507, "PHR": 0.8477, "PHR-CB": 0.8873},
            "FPN": {"CFR":0.8743, "CFR-CB": 0.8789, "PHR": 0.8941, "PHR-CB": 0.8881},
            "LINKNET": {"CFR":0.8546, "CFR-CB": 0.8959, "PHR": 0.8904, "PHR-CB": 0.8941},
            "FAPNET": {"CFR":0.8937, "CFR-CB": 0.8797, "PHR": 0.8590, "PHR-CB": 0.8960}}

    train = {"UNET": {"CFR":0.9084, "CFR-CB": 0.9310, "PHR": 0.8241, "PHR-CB": 0.9480},
            "VNET": {"CFR":0.8158, "CFR-CB": 0.8659, "PHR": 0.8151, "PHR-CB": 0.8589},
            "DNCNN": {"CFR":0.8455, "CFR-CB": 0.8567, "PHR": 0.8266, "PHR-CB": 0.8496},
            "UNET++": {"CFR":0.8063, "CFR-CB": 0.8302, "PHR": 0.8211, "PHR-CB": 0.9153},
            "U2NET": {"CFR":0.9071, "CFR-CB": 0.9014, "PHR": 0.8671, "PHR-CB": 0.9481},
            "ATTUNET": {"CFR":0.8225, "CFR-CB": 0.8392, "PHR": 0.8028, "PHR-CB": 0.9095},
            "FPN": {"CFR":0.8845, "CFR-CB": 0.8654, "PHR": 0.9065, "PHR-CB": 0.9311},
            "LINKNET": {"CFR":0.8465, "CFR-CB": 0.9332, "PHR": 0.9108, "PHR-CB": 0.8985},
            "FAPNET": {"CFR":0.9285, "CFR-CB": 0.9264, "PHR": 0.8241, "PHR-CB": 0.9514}}

    test = {"UNET": {"CFR":0.8306, "CFR-CB": 0.8456, "PHR": 0.8058, "PHR-CB": 0.7930},
            "VNET": {"CFR":0.7463, "CFR-CB": 0.7551, "PHR": 0.7552, "PHR-CB": 0.7573},
            "DNCNN": {"CFR":0.8132, "CFR-CB": 0.8050, "PHR": 0.7959, "PHR-CB": 0.7844},
            "UNET++": {"CFR":0.7777, "CFR-CB": 0.8198, "PHR": 0.7878, "PHR-CB": 0.7664},
            "U2NET": {"CFR":0.7639, "CFR-CB": 0.7898, "PHR": 0.8045, "PHR-CB": 0.7615},
            "ATTUNET": {"CFR":0.7717, "CFR-CB": 0.7579, "PHR": 0.7496, "PHR-CB": 0.7776},
            "FPN": {"CFR":0.8450, "CFR-CB": 0.8651, "PHR": 0.8301, "PHR-CB": 0.6967},
            "LINKNET": {"CFR":0.8021, "CFR-CB": 0.8638, "PHR": 0.8454, "PHR-CB": 0.6996},
            "FAPNET": {"CFR":0.8544, "CFR-CB": 0.8679, "PHR": 0.7649, "PHR-CB": 0.8606}}
    model = {}
    id = 1
    for k in train.keys():
        model[k] = id
        id += 1

    for i in range(3):
        fig = plt.figure(figsize=(12, 6))
        ax = plt.gca()
        
        if i==0:
            meaniou(train, ax, model)
            ax.set_title("TRAIN", fontsize=30, fontweight="bold")
            ax.legend(["CFR", "CFR-CB", "PHR", "PHR-CB"], 
                    prop=dict(weight='bold', size=18),
                    loc = 9, bbox_to_anchor=(0.5, 0.5, -0.55, 0.5))
        elif i==1:
            meaniou(val, ax, model)
            ax.set_title("VALID", fontsize=30, fontweight="bold")
        else:
            meaniou(test, ax, model)

            
            
            ax.set_title("TEST", fontsize=30, fontweight="bold")

        
        plt.savefig((config['visualization_dir']+"MIou"+str(i)+".png"), dpi=800)
        plt.show()


if __name__=='__main__':
    
    config = get_config_yaml('config.yaml', {})
    
    pathlib.Path(config['visualization_dir']).mkdir(parents = True, exist_ok = True)

    
    
    class_balance_check(True, config["p_train_dir"])


    train_dir = pd.read_csv(config['train_dir'])
    print("Train examples: ", len(train_dir))
    print(class_distribution(train_dir))

    test_dir = pd.read_csv(config['test_dir'])
    print("Test examples: ", len(test_dir))
    print(class_distribution(test_dir))

    valid_dir = pd.read_csv(config['valid_dir'])
    print("Valid examples: ", len(valid_dir))
    print(class_distribution(valid_dir))
    
    print("Saving figures....")
    display_all(train_dir)
    display_all(valid_dir)
    display_all(test_dir)
    
    print("Saving color composite figures....")    
    display_color_composite(train_dir)
    display_color_composite(valid_dir)
    display_color_composite(test_dir)
    
    print("Saving comparison figure....")
    save_for_comparison(config)
    
    meaniou_plot(config)
import os

import torch
from omegaconf import OmegaConf

import graph_lib
import noise_lib
import utils
from model import SEDD
from model.ema import ExponentialMovingAverage


def load_model_hf(dir, device):
    score_model = SEDD.from_pretrained(dir).to(device)
    graph = graph_lib.get_graph(score_model.config, device)
    noise = noise_lib.get_noise(score_model.config).to(device)
    return score_model, graph, noise


def load_model_local(root_dir, device, checkpoint_name=None):
    cfg = utils.load_hydra_config_from_run(root_dir)
    graph = graph_lib.get_graph(cfg, device)
    noise = noise_lib.get_noise(cfg).to(device)
    score_model = SEDD(cfg).to(device)
    ema = ExponentialMovingAverage(score_model.parameters(), decay=cfg.training.ema)

    if checkpoint_name is None:
        ckpt_dir = os.path.join(root_dir, "checkpoints-meta", "checkpoint.pth")
    else:
        ckpt_dir = os.path.join(root_dir, checkpoint_name)
    print(f"Loading checkpoint @ {ckpt_dir}")
    loaded_state = torch.load(ckpt_dir, map_location=device, weights_only=False)

    score_model.load_state_dict(loaded_state["model"])
    ema.load_state_dict(loaded_state["ema"])

    ema.store(score_model.parameters())
    ema.copy_to(score_model.parameters())
    return score_model, graph, noise


def load_model(root_dir, device, checkpoint_name=None):
    try:
        return load_model_hf(root_dir, device)
    except:
        return load_model_local(root_dir, device, checkpoint_name)

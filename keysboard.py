#!python
# keysboard for Linux by Dunkmania101


import os
import sys
from threading import Thread
import json
from json import JSONDecodeError
from evdev import InputDevice, categorize, ecodes


##########
# Config:
print_key_codes = True # Whether to print the keycode of each key pressed on the grabbed keyboard. Useful for configuration.
print_actions = True # Whether to print info about each action.
config_file = "./keysboard-conf.json"
universal_exit_key = "KEY_ESC" # Just in case the one in the config doesn't work. Set to something that isn't a keycode to disable.
indent_amount = 4 # Amount in spaces to indent saved Json.

# Defaults
first_device_def = "the_ID_of_a_device" # Default device id to use in newly generated configs.
exit_key_def = "KEY_ESC" # Default exit key in a newly added device.
first_layer_def = "main" # Default name for the first layer in a newly added device.
##########


##########
# Start Script
##########
# Dict Tags/Values
# Action Types
set_layer_action_tag = "set_layer"
shell_action_tag = "shell"

# Keys
exit_key_tag = "exit_key"

# Other
devices_tag = "devices"
layers_tag = "layers"
keybinds_tag = "keybinds"
action_type_tag = "action_type"
action_tag = "action"
backup_tag = "backup"
##########

##########


def blank_layer():
    return {
        keybinds_tag: {
            "KEY_1": {
                action_type_tag: set_layer_action_tag,
                action_tag: first_layer_def
            }
        }
    }


def blank_device():
    return {
        exit_key_tag: exit_key_def,
        layers_tag: {
            first_layer_def: blank_layer()
        }
    }


def blank_config():
    return {
        devices_tag: {
            first_device_def: blank_device()
        }
    }


def open_config(overwrite):
    if not os.path.isfile(config_file):
        f = open(config_file, "x")
        try:
            json.dump(blank_config(), f, indent=indent_amount)
        finally:
            f.close()
    if overwrite:
        return open(config_file, "w+")
    return open(config_file, "r+")


def save_config(config):
    try:
        f = open_config(True)
        json.dump(config, f, indent=indent_amount)
    finally:
        f.close()


def read_config():
    f = open_config(False)
    try:
        try:
            read_conf = f.read()
            conf = json.loads(read_conf)
        except JSONDecodeError:
            blank = blank_config()
            blank[backup_tag] = read_conf
            save_config(blank)
            try:
                read_conf = f.read()
                conf = json.loads(read_conf)
            except JSONDecodeError:
                conf = blank_config()
        return conf
    finally:
        f.close()


def add_device(device):
    config = read_config()
    config[devices_tag][device] = blank_device()
    save_config(config)


def add_layer(device, layer):
    config = read_config()
    config[devices_tag][device][layers_tag][layer] = blank_layer()
    save_config(config)


def add_key(device, layer, key, action_type, action):
    config = read_config()
    config[devices_tag][device][layers_tag][layer][keybinds_tag][key] = {
        action_type_tag: action_type,
        action_tag: action
        }
    save_config(config)


def get_first_layer(device_config):
    layers = list(device_config[layers_tag].keys())
    if len(layers) > 0:
        return layers[0]
    return ""


def run_device(device):
    invalid_msg = f"Device [ {device} ] is invalid, skipping..."
    error_msg = f"Device [ {device} ] hit an error, stopping..."
    config = read_config()
    devices = config[devices_tag]
    if device in devices.keys():
        try:
            dev = InputDevice("/dev/input/by-id/" + device)
            try:
                dev.grab()
                device_config = devices[device]
                current_layer = get_first_layer(device_config)
                for event in dev.read_loop():
                    if event.type == ecodes.EV_KEY:
                        config = read_config()
                        devices = config[devices_tag]
                        if device in devices:
                            device_config = devices[device]
                            key = categorize(event)
                            if key.keystate == key.key_down:
                                code = key.keycode
                                if print_key_codes:
                                    print(f"[ {device} ]: Pressed key: [ {code} ]")
                                exit_key = device_config[exit_key_tag]
                                if code == exit_key or code == universal_exit_key:
                                    print(f"[ {device} ]: Exit key pressed! Quitting...")
                                    break
                                else:
                                    layers = device_config[layers_tag]
                                    if current_layer in layers:
                                        keybinds = layers[current_layer][keybinds_tag]
                                        for key in keybinds.keys():
                                            bind = keybinds[key]
                                            if code == key:
                                                if action_tag in bind.keys():
                                                    action = bind[action_tag]
                                                    action_type = ""
                                                    if action_type_tag in bind:
                                                        action_type = bind[action_type_tag]
                                                    if action_type == shell_action_tag or action_type == "":
                                                        if print_actions:
                                                            print(f"[ {device} ]: Running in system shell: [ {action} ]")
                                                        try:
                                                            os.system(f"sh -c {action} & disown")
                                                        except:
                                                            print(f"Device [ {device} ] hit an error while running shell command [ {action} ], ignoring...")
                                                    elif action_type == set_layer_action_tag:
                                                        if action in layers.keys():
                                                            if print_actions:
                                                                print(f"[ {device} ]: Switching to layer: [ {action} ]")
                                                            current_layer = action
                                                        else:
                                                            print(f"Layer [ {action} ] is not in config for [ {device} ], ignoring...")
                                    else:
                                        current_layer = get_first_layer(device_config)
                        else:
                            break
            except IOError:
                print(f"Device [ {device} ] is already grabbed, skipping...")
            except:
                print(error_msg)
            finally:
                dev.ungrab()
        except:
            print(invalid_msg)
    else:
        print(invalid_msg)


def run_devices():
    for device in read_config()[devices_tag]:
        try:
            Thread(target=run_device, args=(device,)).start()
        except:
            print(f"Device [ {device} ] has failed to start, skipping...")


args = sys.argv
if len(args) > 1:
    usage_msg = """
Usage:

Run normally: python keysboard.py
Add device: python keysboard.py add-device device_name
Add layer to device: python keysboard.py add-device [ device_name ] [ layer_name ]
Add keybind to layer of device: python keysboard.py add-keybind [ device_name ] [ layer_name] [ keycode ] [ action_type ] [ \"action\" ]

Run with different config (must be at end of command!): python keysboard.py [command] [options] config=path/to/config.json

Valid action_type values: shell, set_layer
Valid action values (respectively): any shell command, any layer of same device

Requires python 3!
    """
    config_arg = "config="
    for arg in args:
        if arg.startswith(config_arg):
            config_file = arg.replace(config_arg, "")
    if "help" in args or "h" in args:
        print(usage_msg)
    elif "add-device" in args:
        if len(args) >= 3:
            add_device(args[2])
        else:
            print(usage_msg)
    elif "add-layer" in args:
        if len(args) >= 4:
            add_layer(args[2], args[3])
        else:
            print(usage_msg)
    elif "add-keybind" in args:
        if len(args) > 7:
            add_key(args[2], args[3], args[4], args[5], args[6])
        else:
            print(usage_msg)
    else:
        print(usage_msg)
else:
    run_devices()

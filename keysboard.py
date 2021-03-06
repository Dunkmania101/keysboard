#!python
# Keysboard for Linux by Dunkmania101


import os, sys, subprocess, json
from json import JSONDecodeError
from threading import Thread
from time import sleep
from evdev import InputDevice, uinput, categorize, ecodes


##########
# Config:
print_key_codes = True # Whether to print the keycode of each key pressed on the grabbed keyboard. Useful for configuration.
print_actions = True # Whether to print info about each action.
global config_file
config_file = os.path.expanduser("~/.config/keysboard/keysboard-conf.json") # Path to the JSON config file. Can be overridden from the command line.
universal_exit_key = "KEY_ESC" # Just in case the one in the config doesn't work. Set to something that isn't a keycode to disable.
indent_amount = 4 # Amount in spaces to indent saved Json.
shorten_name_amount = 15 # Amount in characters to shorten long names by for the log. Set to -1 to disable.

# Defaults:
first_device_def = "the_path_to_a_device" # Default device path to use in newly generated configs.
device_nickname_def = "NotARealDevice" # Default nickname given to new devices. Nicknames are used as friendly names when printing.
exit_key_def = "KEY_ESC" # Default exit key in a newly added device.
first_layer_def = "main" # Default name for the first layer in a newly added device.
exit_cmd_default = "echo Keysboard has exited!" # Default command for each newly generated layer to run on exit.
##########


##########
# Start Script
##########
# Dict Tags/Values
# Action Types
set_layer_action_tag = "set_layer"
shell_action_tag = "shell"
keyboard_action_tag = "keyboard"

# Keys
exit_key_tag = "exit_key"

# Other
exit_cmd_tag = "exit_cmd"
devices_tag = "devices"
device_nickname_tag = "device_nickname"
layers_tag = "layers"
keybinds_tag = "keybinds"
action_type_tag = "action_type"
action_tag = "action"
backup_tag = "backup"
keys_tag = "keys"
key_tag = "key"
hold_time_tag = "hold_time"
delay_tag = "delay"
##########

##########
def exec_cmd(cmd):
    subprocess.run(cmd, shell=True, start_new_session=True)


def press_key(code, hold_time=0.2):
    dev = uinput.UInput()
    key = ecodes.ecodes[code]
    dev.write(ecodes.EV_KEY, key, 1)
    sleep(hold_time)
    dev.write(ecodes.EV_KEY, key, 0)


def press_keys(keys):
    for key in keys:
        if delay_tag in key.keys():
            sleep(key[delay_tag])
        press_key(key[key_tag], key[hold_time_tag])


def blank_layer():
    return {
        keybinds_tag: {
            "KEY_1": {
                action_type_tag: set_layer_action_tag,
                action_tag: first_layer_def
            },
            "KEY_2": {
                action_tag: shell_action_tag,
                action_tag: "echo hi"
            }
        }
    }


def blank_device():
    return {
        device_nickname_tag: device_nickname_def,
        exit_cmd_tag: exit_cmd_default,
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


def mkdir_p(directory):
    try:
        os.makedirs(directory)
    except:
        pass


def open_config(overwrite):
    if not os.path.isfile(config_file):
        mkdir_p(os.path.dirname(config_file))
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

    if devices_tag not in config.keys():
        config[devices_tag] = {}
        save_config(config)

    if config.get(devices_tag, {}).get(device, {}) == {}:
        config[devices_tag][device] = blank_device()
        save_config(config)
    return config


def add_layer(device, layer):
    config = add_device(device)

    if layers_tag not in config[devices_tag][device].keys():
        config[devices_tag][device][layers_tag] = {}
        save_config(config)

    if config.get(devices_tag, {}).get(device, {}).get(layers_tag, {}).get(layer, {}) == {}:
        config[devices_tag][device][layers_tag][layer] = blank_layer()
        save_config(config)
    return config


def add_keybind(device, layer, key, action_type, action):
    config = add_layer(device, layer)

    if keybinds_tag not in config[devices_tag][device][layers_tag][layer].keys():
        config[devices_tag][device][layers_tag][layer][keybinds_tag] = {}
        save_config(config)

    if config.get(devices_tag, {}).get(device, {}).get(layers_tag, {}).get(layer, {}).get(keybinds_tag, {}).get(key, {}) == {}:
        config[devices_tag][device][layers_tag][layer][keybinds_tag][key] = {
            action_type_tag: action_type,
            action_tag: action
        }
        save_config(config)
    return config


def get_first_layer(device_config):
    layers = list(device_config[layers_tag].keys())
    if len(layers) > 0:
        return layers[0]
    return ""


def run_device(device):
    device_short = device
    if shorten_name_amount != -1 and len(device_short) > shorten_name_amount:
        device_short = device_short[:shorten_name_amount] + "..."
    dev_no_config_msg = f"Device [ {device_short} ] is not in the configuration, skipping..."
    invalid_dev_msg = f"Device [ {device_short} ] is invalid, skipping..."
    error_msg = f"Device [ {device_short} ] hit an error, stopping..."
    config = read_config()
    devices = config.get(devices_tag, {})
    if device in devices.keys():
        device_short = devices[device].get(device_nickname_tag, device_short)
        try:
            dev = InputDevice(device)
            try:
                dev.grab()
                device_config = devices[device]
                current_layer = get_first_layer(device_config)
                for event in dev.read_loop():
                    if event.type == ecodes.EV_KEY:
                        key = categorize(event)
                        if key.keystate == key.key_down:
                            config = read_config()
                            devices = config.get(devices_tag, {})
                            if device in devices:
                                device_config = devices[device]
                                device_short = device_config.get(device_nickname_tag, device_short)
                                code = key.keycode
                                if print_key_codes:
                                    print(f"[ {device_short} ]: Pressed key: [ {code} ]")
                                exit_key = device_config.get(exit_key_tag, None)
                                if code == exit_key or code == universal_exit_key:
                                    print(f"[ {device_short} ]: Exit key pressed! Quitting...")
                                    if exit_cmd_tag in device_config:
                                        exit_cmd = device_config[exit_cmd_tag]
                                        try:
                                            exec_cmd(exit_cmd)
                                        except:
                                            print(f"Device [ {device_short} ] hit an error while running its exit command [ {exit_cmd} ], ignoring...")
                                    break
                                else:
                                    layers = device_config.get(layers_tag, {})
                                    if current_layer in layers:
                                        keybinds = layers[current_layer].get(keybinds_tag, {})
                                        for key in keybinds.keys():
                                            bind = keybinds[key]
                                            if (isinstance(code, list) and key in code) or (isinstance(code, str) and code == key):
                                                if action_tag in bind.keys():
                                                    action = bind[action_tag]
                                                    action_type = ""
                                                    if action_type_tag in bind:
                                                        action_type = bind[action_type_tag]
                                                    if action_type == shell_action_tag or action_type == "":
                                                        if print_actions:
                                                            print(f"[ {device_short} ]: Running in system shell: [ {action} ]")
                                                        try:
                                                            Thread(target=exec_cmd, args=(action,)).start()
                                                        except:
                                                            print(f"Device [ {device_short} ] hit an error while running shell command [ {action} ], ignoring...")
                                                    elif action_type == keyboard_action_tag:
                                                        if type(action) is list:
                                                            Thread(target=press_keys, args=(action,)).start()
                                                        else:
                                                            Thread(target=press_key, args=(action, bind[hold_time_tag])).start()
                                                    elif action_type == set_layer_action_tag:
                                                        if action in layers.keys():
                                                            if print_actions:
                                                                print(f"[ {device_short} ]: Switching to layer: [ {action} ]")
                                                            current_layer = action
                                                        else:
                                                            print(f"Layer [ {action} ] is not in config for [ {device_short} ], ignoring...")
                                    else:
                                        current_layer = get_first_layer(device_config)
                            else:
                                print(dev_no_config_msg)
                                break
            except IOError:
                print(f"Device [ {device} ] is already grabbed, skipping...")
            except:
                print(error_msg)
            finally:
                dev.ungrab()
        except:
            print(invalid_dev_msg)
    else:
        print(dev_no_config_msg)


def run_devices():
    for device in read_config()[devices_tag]:
        try:
            Thread(target=run_device, args=(device,)).start()
        except:
            print(f"Device [ {device} ] has failed to start, skipping...")


def main_run(args):
    if len(args) > 1:
        invalid_cmdline_msg = "Invalid command line arguments!"
        usage_msg = """
Usage:

Run normally: python keysboard.py
Add device: python keysboard.py add-device device_name
Add layer to device: python keysboard.py add-device [ device_name ] [ layer_name ]
Add keybind to layer of device: python keysboard.py add-keybind [ device_name ] [ layer_name] [ keycode ] [ action_type ] [ \"action\" ]

Run with different config: python keysboard.py [command] [options] config=path/to/config.json

Valid action_type values: shell, set_layer
Valid action values (respectively): any shell command, any layer of same device

Requires python 3!
        """
        def print_usage_msg(invalid_cmdline=False):
            if invalid_cmdline:
                print(invalid_cmdline_msg)
            print(usage_msg)
        config_arg = "config="
        for arg in args:
            if arg.startswith(config_arg):
                global config_file
                config_file = os.path.expanduser(arg.replace(config_arg, ""))
                args.remove(arg)
        if len(args) > 1:
            if "help" in args or "h" in args:
                print(usage_msg)
            elif "add-device" in args:
                if len(args) >= 3:
                    add_device(args[2])
                else:
                    print_usage_msg(True)
            elif "add-layer" in args:
                if len(args) >= 4:
                    add_layer(args[2], args[3])
                else:
                    print_usage_msg(True)
            elif "add-keybind" in args:
                if len(args) >= 7:
                    add_keybind(args[2], args[3], args[4], args[5], args[6])
                else:
                    print_usage_msg(True)
            else:
                print_usage_msg(True)
        else:
            run_devices()
    else:
        run_devices()


if __name__ == "__main__":
    main_run(sys.argv)

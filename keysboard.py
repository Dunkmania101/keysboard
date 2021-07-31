#!python
#################################################
#===============================================#
# |                     Ascii Art :)        | # #
# |                                         | # #
# --------------------------------------------- #
# ---- Keysboard for Linux by Dunkmania101 ---- #
# --------------------------------------------- #
#################################################


import os, sys, subprocess, json
from json import JSONDecodeError
from threading import Thread
from time import sleep
from evdev import InputDevice, uinput, categorize, ecodes


##########
# Config:
universal_exit_key = "KEY_ESC" # Just in case the one in the config doesn"t work. Set to something that isn"t a keycode to disable.
indent_amount = 4 # Amount in spaces to indent saved Json.
shorten_name_amount = 15 # Amount in characters to shorten long names to for the log. Set to -1 to disable.

# Config Defaults:
config_file_def = os.path.expanduser("~/.config/keysboard/keysboard-conf.json") # Path to the default JSON config file. Can be overridden from the command line.
first_device_def = "the_path_to_a_device" # Default device path to use in newly generated configs.
device_nickname_def = "NotARealDevice" # Default nickname given to new devices. Nicknames are used as friendly names when printing.
exit_key_def = "KEY_ESC" # Default exit key in a newly added device.
first_layer_def = "main" # Default name for the first layer in a newly added device.
exit_cmd_default = "echo Keysboard has exited!" # Default command for each newly generated layer to run on exit.
hold_time_def = 0.1 # Default hold time for simulated keypresses (used if nothing is specified in the config).
##########


##########
# Start Script
##########
# Dict Tags/Values
# Action Types
action_set_layer_tag = "set_layer"
action_shell_tag = "shell"
action_keyboard_tag = "keyboard"
action_alias_tag = "alias"
action_multi_tag = "multi"

# Devices
devices_tag = "devices"
device_nickname_tag = "device_nickname"
aliases_tag = "aliases"
exit_key_tag = "exit_key"
exit_cmd_tag = "exit_cmd"

# Layers
layers_tag = "layers"
first_layer_tag = "first_layer"
keybinds_tag = "keybinds"
inherit_tag = "inherit"

# Printing
print_key_codes_tag = "print_key_codes"
print_actions_tag = "print_actions"

# Actions
action_type_tag = "action_type"
action_tag = "action"

# Key Simulation
keys_tag = "keys"
key_tag = "key"
hold_time_tag = "hold_time"
delay_tag = "delay"
set_key_tag = "set_key"

# Other
backup_tag = "backup"
##########

##########
def gen_log_msg(device="", current_layer="", msg="", exclude_empty=True):
    if exclude_empty and device == "":
        device_msg = ""
    else:
        device_msg = f" Device = [ {device} ]"
    if exclude_empty and current_layer == "":
        layer_msg = ""
    else:
        layer_msg = f" / Layer = [ {current_layer} ]"

    if exclude_empty and device_msg == "" and layer_msg == "":
        device_layer_msg = ""
    else:
        device_layer_msg = f"[ {device_msg}{layer_msg} ]: "

    return f"{device_layer_msg}{msg}"


def exec_cmd(cmd, device="", current_layer="", print_output=True):
    output = str(subprocess.run(cmd, shell=True, start_new_session=True, stdout=subprocess.PIPE).stdout.decode("utf-8"))
    if print_output and output != "" and output != "\n":
        if "\n" in output:
            output = "|".join(output.splitlines())
        print(gen_log_msg(device, current_layer, f"Command output: [ {output} ]"))

def run_thread(target, args):
    Thread(target=target, args=args, daemon=False).start()


def set_key(code, state=0, dev=uinput.UInput()):
    key = ecodes.ecodes[code]
    dev.write(ecodes.EV_KEY, key, state)
    dev.syn()

def press_key(code, hold_time=hold_time_def, dev=uinput.UInput()):
    set_key(code, 1, dev)
    sleep(hold_time)
    set_key(code, 0, dev)

def press_keys(keys, dev=uinput.UInput()):
    for key in keys:
        if set_key_tag in key.keys():
            set_key(key[key_tag], key[set_key_tag], dev)
        else:
            if delay_tag in key.keys():
                sleep(key[delay_tag])
            press_key(key[key_tag], key.get(hold_time_tag, hold_time_def), dev)


def blank_layer():
    return {
        keybinds_tag: {
            "KEY_1": {
                action_type_tag: action_set_layer_tag,
                action_tag: first_layer_def
            },
            "KEY_2": {
                action_tag: action_shell_tag,
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


def open_config(overwrite, config_file):
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

def save_config(config, config_file):
    try:
        f = open_config(True, config_file)
        json.dump(config, f, indent=indent_amount)
    finally:
        f.close()

def read_config(config_file):
    f = open_config(False, config_file)
    try:
        try:
            read_conf = f.read()
            conf = json.loads(read_conf)
        except JSONDecodeError:
            blank = blank_config()
            blank[backup_tag] = read_conf
            save_config(blank, config_file)
            try:
                read_conf = f.read()
                conf = json.loads(read_conf)
            except JSONDecodeError:
                conf = blank_config()
        return conf
    finally:
        f.close()


def add_device(device, config_file):
    config = read_config(config_file)

    if devices_tag not in config.keys():
        config[devices_tag] = {}
        save_config(config, config_file)

    if config.get(devices_tag, {}).get(device, {}) == {}:
        config[devices_tag][device] = blank_device()
        save_config(config, config_file)
    return config

def add_layer(device, layer, config_file):
    config = add_device(device, config_file)

    if layers_tag not in config[devices_tag][device].keys():
        config[devices_tag][device][layers_tag] = {}
        save_config(config, config_file)

    if config.get(devices_tag, {}).get(device, {}).get(layers_tag, {}).get(layer, {}) == {}:
        config[devices_tag][device][layers_tag][layer] = blank_layer()
        save_config(config, config_file)
    return config

def add_keybind(device, layer, key, action_type, action, config_file):
    config = add_layer(device, layer, config_file)

    if keybinds_tag not in config[devices_tag][device][layers_tag][layer].keys():
        config[devices_tag][device][layers_tag][layer][keybinds_tag] = {}
        save_config(config, config_file)

    if config.get(devices_tag, {}).get(device, {}).get(layers_tag, {}).get(layer, {}).get(keybinds_tag, {}).get(key, {}) == {}:
        config[devices_tag][device][layers_tag][layer][keybinds_tag][key] = {
            action_type_tag: action_type,
            action_tag: action
        }
        save_config(config, config_file)
    return config


def get_first_layer(device_config):
    layers = list(device_config[layers_tag].keys())
    if len(layers) > 0:
        return layers[0]
    return ""

class StringContainer():
    string = ""
    def set_string(self, string):
        if isinstance(string, str):
            self.string = string
    def get_string(self):
        return self.string
    def __eq__(self, other):
        return (isinstance(other, (str, StringContainer)) and other == self.get_string()) or super.__eq__(self, other)
    def __str__(self):
        return self.get_string()

def run_device(device, config_file):
    device_short = device
    if shorten_name_amount != -1 and len(device_short) > shorten_name_amount:
        device_short = device_short[:shorten_name_amount] + "..."
    dev_no_config_msg = f"Device [ {device_short} ] is not in the configuration, skipping..."
    invalid_dev_msg = f"Device [ {device_short} ] is invalid, skipping..."
    error_msg = gen_log_msg(device_short, "", f"Hit a critical error, stopping...")
    config = read_config(config_file)
    devices = config.get(devices_tag, {})
    if device in devices.keys():
        device_short = devices[device].get(device_nickname_tag, device_short)
        try:
            dev = InputDevice(device)
            try:
                dev.grab()
                device_config = devices[device]
                current_layer = StringContainer()
                def set_layer_default():
                    current_layer.set_string(device_config.get(first_layer_tag, get_first_layer(device_config)))
                set_layer_default()
                fake_dev = uinput.UInput()
                for event in dev.read_loop():
                    if event.type == ecodes.EV_KEY:
                        key = categorize(event)
                        if key.keystate == key.key_down:
                            config = read_config(config_file)
                            devices = config.get(devices_tag, {})
                            if device in devices:
                                device_config = devices[device]
                                device_aliases = device_config.get(aliases_tag, {})
                                device_short = device_config.get(device_nickname_tag, device_short)
                                code = key.keycode
                                if print_key_codes_tag in device_config.keys():
                                    print_key_codes = device_config[print_key_codes_tag]
                                else:
                                    print_key_codes = True
                                if print_key_codes:
                                    print(gen_log_msg(device_short, current_layer.get_string(), f"Pressed key: [ {code} ]"))
                                exit_key = device_config.get(exit_key_tag, None)
                                if code == exit_key or code == universal_exit_key:
                                    print(gen_log_msg(device_short, current_layer.get_string(), "Exit key pressed! Quitting..."))
                                    if exit_cmd_tag in device_config:
                                        exit_cmd = device_config[exit_cmd_tag]
                                        if isinstance(exit_cmd, str):
                                            try:
                                                run_thread(exec_cmd, (exit_cmd,))
                                            except:
                                                print(gen_log_msg(device_short, current_layer.get_string(), f"Device [ {device_short} ] hit an error while running its exit command [ {exit_cmd} ], ignoring..."))
                                    break
                                else:
                                    layers = device_config.get(layers_tag, {})
                                    if current_layer.get_string() in layers:
                                        keybinds = {}
                                        inherited_layers = layers[current_layer.get_string()].get(inherit_tag, [])
                                        if isinstance(inherited_layers, str) and inherited_layers in layers.keys():
                                            inherited_layers = layers[inherited_layers]
                                        if isinstance(inherited_layers, list):
                                            for inherited_layer in inherited_layers:
                                                if inherited_layer in layers:
                                                    keybinds.update(layers[inherited_layer].get(keybinds_tag, {}))
                                        keybinds.update(layers[current_layer.get_string()].get(keybinds_tag, {}))
                                        for key in keybinds.keys():
                                            if (isinstance(code, list) and key in code) or (isinstance(code, str) and code == key):
                                                old_aliases = []
                                                def exec_action(bind):
                                                    if action_tag in bind.keys():
                                                        action = bind[action_tag]
                                                        action_type = ""
                                                        if print_actions_tag in device_config:
                                                            print_actions = device_config[print_actions_tag]
                                                        else:
                                                            print_actions = True
                                                        if action_type_tag in bind:
                                                            action_type = bind[action_type_tag]
                                                        if action_type == action_shell_tag or action_type == "":
                                                            if print_actions:
                                                                print(gen_log_msg(device_short, current_layer.get_string(), f"Running in system shell: [ {action} ]"))
                                                            try:
                                                                run_thread(exec_cmd, (action, device_short, current_layer.get_string(), print_actions,))
                                                            except:
                                                                print(gen_log_msg(device_short, current_layer.get_string(), f"Hit an error while running shell command [ {action} ], ignoring..."))
                                                        elif action_type == action_keyboard_tag:
                                                            if type(action) is list:
                                                                run_thread(press_keys, (action, fake_dev,))
                                                            elif key_tag in action.keys():
                                                                code = action[key_tag]
                                                                if set_key_tag in action.keys():
                                                                    run_thread(set_key, (code, bind[set_key_tag], fake_dev,))
                                                                else:
                                                                    run_thread(press_key, (code, bind.get(hold_time_tag, hold_time_def,), fake_dev))
                                                        elif action_type == action_set_layer_tag:
                                                            if action in layers.keys():
                                                                if print_actions:
                                                                    print(gen_log_msg(device_short, "", f"Switching to layer: [ {action} ], From Layer: [ {current_layer.get_string()} ]"))
                                                                current_layer.set_string(action)
                                                            else:
                                                                print(gen_log_msg(device_short, current_layer.get_string(), f"Layer [ {action} ] is not in config, ignoring..."))
                                                        elif action_type == action_alias_tag:
                                                            if action in device_aliases.keys():
                                                                if action in old_aliases:
                                                                    print(gen_log_msg(device_short, current_layer.get_string(), f"Action alias [ {action} ] has been recursively called, skipping..."))
                                                                else:
                                                                    old_aliases.append(action)
                                                                    exec_action(device_aliases[action])
                                                            else:
                                                                print(gen_log_msg(device_short, current_layer.get_string(), f"Action alias [ {action} ] is undefined, skipping..."))
                                                        elif action_type == action_multi_tag:
                                                            if isinstance(action, list):
                                                                for sub_action in action:
                                                                    exec_action(sub_action)
                                                                    if isinstance(sub_action, dict):
                                                                        sub_action_type = sub_action.get(action_type_tag, "")
                                                                        if sub_action_type == action_alias_tag and action_tag in sub_action and sub_action[action_tag] in old_aliases:
                                                                            old_aliases.remove(sub_action[action_tag])
                                                            else:
                                                                print(gen_log_msg(device, current_layer.get_string(), f"Multi-Action [ {action} ] is not of type list, skipping..."))
                                                exec_action(keybinds[key])
                                    else:
                                        set_layer_default()
                            else:
                                print(dev_no_config_msg)
                                break
            except IOError:
                print(gen_log_msg(device_short, "", "Already grabbed, skipping..."))
                pass
            except Exception as error:
                print(f"{error_msg}: {str(error)}")
                pass
            finally:
                try:
                    dev.ungrab()
                except IOError:
                    pass
                fake_dev.close()
        except IOError:
            print(invalid_dev_msg)
            pass
    else:
        print(dev_no_config_msg)


def run_devices(config_file):
    for device in read_config(config_file).get(devices_tag, {}).keys():
        try:
            run_thread(run_device, (device, config_file,))
        except Exception as error:
            print(gen_log_msg(device, "", f"Failed to start, skipping...: {str(error)}"))
            pass


def main_run(args):
    config_file = config_file_def
    if len(args) > 1:
        invalid_cmdline_msg = "Invalid command line arguments!"
        usage_msg = """
Usage:

Run normally: python keysboard.py
Add device: python keysboard.py add-device device_name
Add layer to device: python keysboard.py add-device device_name layer_name
Add keybind to layer of device: python keysboard.py add-keybind device_name layer_name keycode action_type \"action\"

Run with different config: python keysboard.py command options config=path/to/config.json

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
            run_devices(config_file)
    else:
        run_devices(config_file)


if __name__ == "__main__":
    main_run(sys.argv)

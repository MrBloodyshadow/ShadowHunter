# -*- coding: utf-8 -*-

import configparser


def config_file_exists(filename):
    config = configparser.ConfigParser()
    try:
        with open(filename) as f:
            config.read(f)
            f.close()
    except IOError:
        raise


def validate_ini_file(filename, sections):
    try:
        config_file_exists(filename)
        valid = True
    except IOError as e:
        print(e)
        valid = False

    if valid:
        config = configparser.ConfigParser()
        config.read(filename)

        if type(sections) is list:
            for section in sections:
                valid = check_section(filename, config, section) and valid
        else:
            valid = check_section(filename, config, sections)

        return valid


def check_section(filename, config, section):
    valid = True
    section_name = section[0]
    if not config.has_section(section_name):
        print('Section "{}" is missing in the "{}" file.'.format(section_name, filename))
        valid = False
    else:
        section_values = config[section_name]
        section_options = section[1]
        for option in section_options:
            if not config.has_option(section_name, option):
                print('Option "{}" in section "{}" is missing in the "{}" file.'.
                      format(option, section_name, filename))
                valid = False
            else:
                if len(section_values[option]) == 0:
                    print('Option "{}" in section "{}" is blank in the "{}" file.'.
                          format(option, section_name, filename))
                    valid = False

    return valid

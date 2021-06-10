'''util.funcs

This module contains utility functions
'''
import numpy as np
import pandas as pd
import json
import logging
from collections import namedtuple


RunConfig = namedtuple(
    'RunConfig', ['pearls_needed', 'rods_needed', 'looting_lvl'],
    defaults=[12, 6, 0]
)


def parse_datapack(filename):
    '''
    This method parses the inputted databack, returning a parsed dictionary
    for use in the rest of the program.

    If the path is unknown or there is an error in opening the file, an empty
    dirct is returned.

    Parameters:
        :param filename: (str) The path to the datapack

    Returns:
        dict: The parsed datapack or empty in case of an error
    '''
    retval = {}
    try:
        with open(filename, 'r') as f:
            raw_pack = json.load(f)
        
        pool = raw_pack['pools'][0]
        retval['rolls'] = pool['rolls']
        retval['entries'] = pool['entries']
        retval['num_entries'] = len(pool['entries'])
        retval['entry_by_item'] = {entry['name']: entry for entry in retval['entries']}
        retval['entry_index'] = {entry['name']: i for entry, i in zip(retval['entries'], range(retval['num_entries']))}
        
        # Calculate probability distribution for weighted RNG
        prob = np.empty(retval['num_entries'], dtype=np.float)
        total_weight = 0
        for i, entry in zip(range(retval['num_entries']), retval['entries']):
            weight = 1
            if('weight' in entry):
                weight = np.float(entry['weight'])
            prob[i] = weight
            total_weight += weight
        retval['prob'] = prob / np.float(total_weight)
    except Exception as e:
        logging.error('Error opening file {}'.format(e))

    return retval


def get_drop(entity, rng):
    '''
    This method returns a dict containing the item and quantity from a drop

    Parameters:
        :param entity: (dict) The entity to get a drop from
        :param rng: (np.random.Generator) The random number generator to use

    Returns:
        dict: The item dropped
    '''
    retval = {'name': entity['name']}

    quantity = -1
    if('functions' in entity):
        for function in entity['functions']:
            if(function['function'] not in ['minecraft:set_count']):
                continue

            # Calculate quantity
            drop = function['count']
            if(drop['type'] == 'minecraft:uniform'):
                quantity = int(np.round(rng.uniform(low=drop['min'], high=drop['max'])))
       
    # I we don't have a quantity, it means we had no function to set it,
    # in this case, we assume 1
    if(quantity == -1):
        quantity = 1
    
    retval['quantity'] = quantity

    return retval


def simulate_rolls(datapack, rng):
    '''
    This method simulates rolling on a loot table, returning the item obtained

    Parameters:
        :param entity: (dict) The datapack to use
        :param rng: (np.random.Generator) The random number generator to use

    Returns:
        dict: The item obtained
    '''
    # Prepare return value
    retval = {'rolls': datapack['rolls'], 'drops': []}

    # Roll the table
    for i in range(datapack['rolls']):
        # First get the item to obtained
        item_index = rng.choice(range(datapack['num_entries']), p=datapack['prob'])

        # Add drop
        retval['drops'].append(get_drop(datapack['entries'][item_index], rng))

    return retval


def simulate_run(barter_pack, blaze_pack, barter_rng=np.random.default_rng(), blaze_rng=np.random.default_rng(), config=RunConfig()):
    '''
    This function simulates performing one run.

    This simulation simply checks how many barters need to be completed and 
    blazes need to be killed in order to be able to complete Minecraft.

    Bartering and entity kills (blazes) use different random number generators in the game.

    The configuration options for the run currently include:
        - pearls_needed: The number of pearls needed
        - rods_needed: The number of blaze rods needed
        - looting_level: The player's looting level

    The return will be a dictionary with the summary of the run:
    {
        "pearls_needed": int,
        "pearls_bartered": int,
        "barters_done": int,
        "rods_needed": int,
        "rods_got": int,
        "blazes_killed": int
    }

    Parameters:
        :param barter_pack: (dict) The bartering datapack
        :param blaze_pack: (dict) The blaze datapack
        :param barter_rng: (np.random.Generator) RNG to use for bartering
        :param blaze_rng: (np.random.Generator) RNG to use for blaze kills
        :param config: (RunConfig) Configuration options for the run

    Returns:
        dict: Run summary
    '''
    # Initialize return value
    retval = {
        "pearls_needed": config.pearls_needed,
        "pearls_bartered": 0,
        "barters_done": 0,
        "rods_needed": config.rods_needed,
        "rods_got": 0,
        "blazes_killed": 0
    }

    # Start playing Minecraft
    # We will do barters first
    while(retval["pearls_bartered"] < retval["pearls_needed"]):
        retval["barters_done"] += 1
        cur_barter = simulate_rolls(barter_pack, barter_rng)
        for roll in cur_barter["drops"]:
            if(roll["name"] == "minecraft:ender_pearl"):
                # Success!
                retval["pearls_bartered"] += roll["quantity"]

    # Now kill some fire bois
    while(retval["rods_got"] < retval["rods_needed"]):
        retval["blazes_killed"] += 1
        cur_kill = simulate_rolls(blaze_pack, blaze_rng)
        for roll in cur_kill["drops"]:
            if(roll["name"] == "minecraft:blaze_rod"):
                # Success!
                retval["rods_got"] += roll["quantity"]

    # All done!
    return retval
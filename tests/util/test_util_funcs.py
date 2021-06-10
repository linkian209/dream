'''test.test_util_funcs

This module contains the utility functions
'''
import pytest
import numpy as np
from src.util.funcs import parse_datapack, get_drop, simulate_rolls, simulate_run, RunConfig

@pytest.fixture
def barter_datapack(datadir):
    return datadir.join('barter.json')

@pytest.fixture
def blaze_datapack(datadir):
    return datadir.join('blaze.json')

@pytest.fixture
def test_entities():
    return {
        "no_func": {
          "type": "minecraft:item",
          "weight": 40,
          "name": "minecraft:obsidian"
        },
        "func_no_type": {
          "type": "minecraft:item",
          "weight": 5,
          "functions": [
            {
              "function": "minecraft:enchant_randomly",
              "enchantments": [
                "minecraft:soul_speed"
              ]
            }
          ],
          "name": "minecraft:book"
        },
        "func_uniform": {
          "type": "minecraft:item",
          "weight": 10,
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": {
                "min": 2.0,
                "max": 4.0,
                "type": "minecraft:uniform"
              }
            }
          ],
          "name": "minecraft:ender_pearl"
        }
    }


# parse_datapack tests
def test_parse_datapack(barter_datapack):
    '''
    This tests that the parsed output contains the keys expected
    '''
    retval = parse_datapack(barter_datapack)
    assert('prob' in retval)
    assert('num_entries' in retval)
    assert('entry_by_item' in retval)
    assert('entry_index' in retval)
    assert('rolls' in retval)
    assert('entries' in retval)

def test_entry_by_item_mapping(barter_datapack):
    retval = parse_datapack(barter_datapack)
    test_entry = retval['entries'][0]
    assert(test_entry == retval['entry_by_item'][test_entry['name']])

def test_entry_index(barter_datapack):
    retval = parse_datapack(barter_datapack)
    test_entry = 'minecraft:ender_pearl'
    assert(retval['entry_index'][test_entry] == 6)

def test_prob_datapack(barter_datapack):
    '''
    This tests that the prob distribution is correctly calculated
    '''
    retval = parse_datapack(barter_datapack)
    probs = retval['prob']
    sum_probs = sum(probs)
    assert(np.abs(sum_probs - 1) <= np.finfo(np.float).eps)

def test_bad_file_datapack_parse():
    '''
    This tests that a file error returns an empty dict
    '''
    retval = parse_datapack('')
    assert(retval == {})


# get_drop tests
def test_get_drop_no_func(test_entities):
    '''
    This tests that we return a single item when there
    is no function for an entity
    '''
    rng = np.random.default_rng(seed=0)
    retval = get_drop(test_entities['no_func'], rng)
    assert(retval['quantity'] == 1)

def test_get_drop_func_no_type(test_entities):
    '''
    This tests that we return a single item when there are no supported
    drop types
    '''
    rng = np.random.default_rng(seed=0)
    retval = get_drop(test_entities['func_no_type'], rng)
    assert(retval['quantity'] == 1)

def test_get_drop_func_uniform(test_entities):
    '''
    This tests that we return a number of items within the uniform distribution
    for the item
    '''
    rng = np.random.default_rng(seed=0)
    for i in range(100):
        retval = get_drop(test_entities['func_uniform'], rng)
        function = test_entities['func_uniform']['functions'][0]['count']
        assert(retval['quantity'] >= function['min'])
        assert(retval['quantity'] <= function['max'])


# simulate_rolls tests
def test_single_barter(barter_datapack):
    '''
    This tests that we return a single barter in the expected format
    '''
    datapack = parse_datapack(barter_datapack)
    rng = np.random.default_rng(seed=0)
    test_drop = {'drops': [{'name': 'minecraft:soul_sand', 'quantity': 4}], 'rolls': 1}
    drop = simulate_rolls(datapack, rng)
    assert(drop == test_drop)

def test_single_blaze_kill(blaze_datapack):
    '''
    This tests that we return a single kill in the expected format
    '''
    datapack = parse_datapack(blaze_datapack)
    rng = np.random.default_rng(seed=0)
    test_drop = {'drops': [{'name': 'minecraft:blaze_rod', 'quantity': 0}], 'rolls': 1}
    drop = simulate_rolls(datapack, rng)
    assert(drop == test_drop)


# simulate_run tests
def test_simulate_run(barter_datapack, blaze_datapack):
    '''
    This test simulates a default settings run, returning the results of the run.

    A default settings run will require 12 pearls and 6 blaze rods. This
    requires at least 3 barters (max of 4 per barter) and 6 blaze kills.
    '''
    barter_pack = parse_datapack(barter_datapack)
    barter_rng = np.random.default_rng(seed=0)
    blaze_pack = parse_datapack(blaze_datapack)
    blaze_rng = np.random.default_rng(seed=0)
    retval = simulate_run(barter_pack, blaze_pack, barter_rng=barter_rng, blaze_rng=blaze_rng)
    assert(type(retval) == dict)
    assert(retval["pearls_needed"] == 12)
    assert(retval["pearls_bartered"] >= 12)
    assert(retval["barters_done"] >= 3)
    assert(retval["rods_needed"] == 6)
    assert(retval["rods_got"] >= 6)
    assert(retval["blazes_killed"] >= 6)

def test_different_pearl_qty(barter_datapack, blaze_datapack):
    '''
    This test simulates runs with less than default pearl quantity
    '''
    barter_pack = parse_datapack(barter_datapack)
    barter_rng = np.random.default_rng(seed=0)
    blaze_pack = parse_datapack(blaze_datapack)
    blaze_rng = np.random.default_rng(seed=0)
    config = RunConfig(pearls_needed=10)
    retval = simulate_run(barter_pack, blaze_pack, barter_rng=barter_rng, blaze_rng=blaze_rng, config=config)
    assert(retval["pearls_needed"] == 10)
    assert(retval["pearls_bartered"] >= 10)
    assert(retval["barters_done"] >= 3)
    assert(retval["rods_needed"] == 6)
    assert(retval["rods_got"] >= 6)
    assert(retval["blazes_killed"] >= 6)

def test_different_rod_qty(barter_datapack, blaze_datapack):
    '''
    This test simulates runs with less than default rod quantity
    '''
    barter_pack = parse_datapack(barter_datapack)
    barter_rng = np.random.default_rng(seed=0)
    blaze_pack = parse_datapack(blaze_datapack)
    blaze_rng = np.random.default_rng(seed=0)
    config = RunConfig(rods_needed=4)
    retval = simulate_run(barter_pack, blaze_pack, barter_rng=barter_rng, blaze_rng=blaze_rng, config=config)
    assert(retval["pearls_needed"] == 12)
    assert(retval["pearls_bartered"] >= 12)
    assert(retval["barters_done"] >= 3)
    assert(retval["rods_needed"] == 4)
    assert(retval["rods_got"] >= 4)
    assert(retval["blazes_killed"] >= 4)
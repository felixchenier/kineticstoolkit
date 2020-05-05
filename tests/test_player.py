#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright Félix Chénier 2020
"""
Tests for ktk.Player
"""
import ktk
import matplotlib.pyplot as plt

def test_instanciate():
    """Test that instanciating a Player does not crash."""

    # Load markers
    kinematics = ktk.loadmat(
        ktk.config['RootFolder'] +
        '/tutorials/data/inversedynamics/basketball_kinematics.mat')

    kinematics = kinematics['kinematics']

    # The player can be instanciated to show markers
    pl = ktk.Player(
        markers=kinematics['Markers'], target=[-5, 0, 0])
    plt.pause(0.01)
    pl.close()

    # The player can be instanciated to show rigid bodies
    pl = ktk.Player(
        rigid_bodies=kinematics['VirtualRigidBodies'],
        target=[-5, 0, 0])
    plt.pause(0.01)
    pl.close()

    # Or the player can be instanciated to show both markers and rigid bodies
    pl = ktk.Player(
        markers=kinematics['Markers'],
        rigid_bodies=kinematics['VirtualRigidBodies'],
        target=[-5, 0, 0])
    plt.pause(0.01)
    pl.close()

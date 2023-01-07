
import io

import matplotlib
import matplotlib.pyplot as plt

from itertools import islice

from dynmap import world
from shapely.geometry import Point, Polygon

from dynmap.tracking import Tracking

import typing

def save_graph(data : dict, title : str, x : str, y : str, chartType, highlight : int = None):
        
    color = "silver"

    matplotlib.rcParams['text.color'] = color
    matplotlib.rcParams['axes.labelcolor'] = color
    matplotlib.rcParams['xtick.color'] = color
    matplotlib.rcParams['ytick.color'] = color
    matplotlib.rcParams["axes.edgecolor"] = color
    matplotlib.rcParams["xtick.labelsize"] = 7

    fig = plt.figure()
    fig.patch.set_facecolor('#2F3136')

    ax = plt.axes()
    ax.patch.set_facecolor('#202225')

    barlist = chartType(data.keys(), data.values())
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)

    plt.xticks(rotation=270)
    plt.subplots_adjust(bottom=0.3)

    if highlight:
        
        barlist[highlight].set_color('r')

    buf = io.BytesIO()
    plt.savefig(buf, facecolor=fig.get_facecolor(), dpi=300)
    buf.seek(0)

    plt.close()

    return buf

def plot_world(world : world.World, plot_players = False, tracking : Tracking = None):

    xw = 36865
    yw = 18432
        
    color = "silver"

    matplotlib.rcParams['text.color'] = color
    matplotlib.rcParams['axes.labelcolor'] = color
    matplotlib.rcParams['xtick.color'] = color
    matplotlib.rcParams['ytick.color'] = color
    matplotlib.rcParams["axes.edgecolor"] = color
    matplotlib.rcParams["xtick.labelsize"] = 7

    fig = plt.figure()
    fig.patch.set_facecolor('#2F3136')

    

    img = plt.imread("earth.png")
    plt.imshow(img, extent=[0-xw, xw, 0-yw, yw], origin='lower')

    for town in world.towns:

        for point_polygon in town.points:

            points = [(p[0], p[1]) for p in point_polygon]

            poly = Polygon(points)
            plt.plot(*poly.exterior.xy, linewidth=0.3, color=town.border_color, zorder=3)
    
    if plot_players:
        x_online = []
        z_online = []

        x_offline = []
        z_offline = []

        for player in tracking.players:
            if player.name in [p.name for p in world.players]:
                x_online.append(player.last_x)
                z_online.append(player.last_z)
            else:
                x_offline.append(player.last_x)
                z_offline.append(player.last_z)
    
        
        plt.scatter(x_online, z_online, color="white", s=10, zorder=5)
        plt.scatter(x_offline, z_offline, color="#707070", s=1, zorder=4)
        


    plt.title(f"RulerCraft Earth ({len(world.towns)} towns)")

    plt.xticks(rotation=270)
    plt.subplots_adjust(bottom=0.3)

    plt.xlim([0-xw, xw])
    plt.ylim([yw, 0-yw])

    buf = io.BytesIO()
    plt.savefig(buf, facecolor=fig.get_facecolor(), dpi=500)
    buf.seek(0)

    plt.close()

    return buf

def plot_towns(towns : typing.List[world.Town]):

    xw = 36865
    yw = 18432
        
    color = "silver"

    matplotlib.rcParams['text.color'] = color
    matplotlib.rcParams['axes.labelcolor'] = color
    matplotlib.rcParams['xtick.color'] = color
    matplotlib.rcParams['ytick.color'] = color
    matplotlib.rcParams["axes.edgecolor"] = color
    matplotlib.rcParams["xtick.labelsize"] = 7

    fig = plt.figure()
    fig.patch.set_facecolor('#2F3136')

    for town in towns:

        for point_polygon in town.points:

            points = [(p[0], p[1]) for p in point_polygon]

            poly = Polygon(points)
            plt.plot(*poly.exterior.xy, linewidth=0.5, color=town.border_color, zorder=3)

            xs, ys = poly.exterior.xy    
            plt.fill(xs, ys, alpha=0.2, fc=town.fill_color, ec='none')

    plt.xticks(rotation=270)

    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')

    ax.invert_yaxis()

    plt.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, facecolor=fig.get_facecolor(), dpi=500, bbox_inches='tight')
    buf.seek(0)

    plt.close()

    return buf

def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))
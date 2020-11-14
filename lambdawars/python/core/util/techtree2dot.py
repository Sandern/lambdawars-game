import os
try:
    import pydot
except ImportError:
    pydot = None
    
from core.units.info import dbunits
from core.abilities.info import dbabilities
from core.abilities import GetTechNode, SubMenu, AbilityMenuBase
from core.factions import dbfactions
from gameinterface import concommand

# Methods to add edges between nodes based on the abilities an ability has.
def AddEdges(info, node, graph, nodes):
    try: abilities = info.abilities
    except AttributeError: abilities = None
    try: successorability = info.successorability
    except AttributeError: successorability = None
    try: transform_type = info.transform_type
    except AttributeError: transform_type = None
    
    if abilities:
        for name in abilities.values():
            if issubclass(dbabilities[name], AbilityMenuBase):
                AddEdges(name, node, graph, nodes)
                continue
            if name in nodes:
                graph.add_edge(pydot.Edge(node, nodes[name]))
                
    if successorability and successorability in nodes:
        graph.add_edge(pydot.Edge(node, nodes[successorability]))
        AddEdges(dbabilities[successorability], nodes[successorability], graph, nodes)
    
    if transform_type and transform_type in nodes:
        graph.add_edge(pydot.Edge(node, nodes[transform_type]))
        AddEdges(dbabilities[transform_type], nodes[transform_type], graph, nodes)
    
def CreateEdges(graph, nodes):
    for name, node in nodes.items():
        if issubclass(dbabilities[name], AbilityMenuBase):
            continue
        AddEdges(dbabilities[name], node, graph, nodes)


def ParseAbilitiesTree():
    """ Turn all abilities in the dbabilities dict into nodes. 
        Then create edges by walking the abilities dicts of
        the abilities (mainly of units and buildings). """
    if not pydot:
        PrintWarning("ParseAbilitiesTree: pydot missing!\n")
        return
    graph = pydot.Dot(graph_type='digraph')
    
    # Create nodes
    nodes = {}
    for name, info in dbabilities.items():
        nodes[name] = pydot.Node(name, style="filled", fillcolor=info.fillcolor)
        
    # Add nodes to graph, filter some of them.
    for name, node in nodes.items():
        if issubclass(dbabilities[name], AbilityMenuBase):
            continue
        graph.add_node(node)
        
    # Create edges
    CreateEdges(graph, nodes)
        
    path = 'stats/trees/abilities.png'
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    graph.write_png(path)
    
def RecursiveCreateNodes(info, nodes):
    if info.name in nodes:
        return
        
    nodes[info.name] = pydot.Node(info.name, style="filled", fillcolor=info.fillcolor)
    
    try: abilities = info.abilities
    except AttributeError: abilities = None
    try: successorability = info.successorability
    except AttributeError: successorability = None
    try: transform_type = info.transform_type
    except AttributeError: transform_type = None
        
    if abilities:
        for name in abilities.values():
            RecursiveCreateNodes(dbabilities[name], nodes)
                
    if successorability:
        RecursiveCreateNodes(dbabilities[successorability], nodes)
        
    if transform_type:
        RecursiveCreateNodes(dbabilities[transform_type], nodes)
        
def ParseAbilitiesTreeFactions():
    if not pydot:
        Warning("ParseAbilitiesTreeFactions: pydot missing!\n")
        return
 
    # Generate graphs per faction
    for faction in dbfactions.values():
        nodes = {}
        graph = pydot.Dot(graph_type='digraph')
        
        RecursiveCreateNodes(dbabilities[faction.startbuilding], nodes)
        
        # Add nodes to graph, filter some of them.
        for name, node in nodes.items():
            if issubclass(dbabilities[name], AbilityMenuBase):
                continue
            graph.add_node(node)
            
        # Create edges
        CreateEdges(graph, nodes)
        
        path = 'stats/trees/%s.png' % (faction.name)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
    
        graph.write_png(path)
        
@concommand('generate_abilitiestree')
def CCGenerateAbilitiesTree(args):
    ParseAbilitiesTree()
    
@concommand('generate_abilitiestree_factions')
def CCGenerateAbilitiesTreeFactions(args):
    ParseAbilitiesTreeFactions()
    
        
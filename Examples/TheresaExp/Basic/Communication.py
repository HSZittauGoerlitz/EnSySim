""" Functions to manage the communication with THERESA GateWay """
from opcua.ua.uaerrors import UaStatusCodeError
from opcua import Client, ua

# Fixed Parameter in THERESA GateWay
CERT = "D:/cert.pem"
KEY = "D:/key.pem"
SECURITY_STRING = "Basic256Sha256,SignAndEncrypt,{},{}".format(CERT, KEY)
APP_URI = "urn:HiLExperiment:client"
# Prepare True value once
DV_TRUE = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
DV_TRUE.ServerTimestamp = None
DV_TRUE.SourceTimestamp = None
DV_FALSE = ua.DataValue(ua.Variant(False, ua.VariantType.Boolean))
DV_FALSE.ServerTimestamp = None
DV_FALSE.SourceTimestamp = None


def ackModelStep(stepModelNode):
    stepModelNode.set_value(DV_FALSE)


def checkModelStep(stepModelNode):
    if stepModelNode.get_value():
        return True
    return False


def createClient(pw):
    client = Client(url='opc.tcp://141.46.119.188:4840/')
    client.set_user('admin')
    client.set_password(pw)
    client.set_security_string(SECURITY_STRING)
    client.application_uri = APP_URI

    return client


def initClient(client):
    client.connect()
    # init method for custom types
    client.load_type_definitions()


def getDeviceSetNode(client):
    # get starting node
    objects = client.get_objects_node()

    for node in objects.get_children():
        if node.get_display_name().Text == "DeviceSet":
            return node

    print("ERROR: DeviseSet Node not found")


# common server browsing functions
def getPrgNode(Node, prgName="PLC_PRG"):
    # Catch bad node configuration
    try:
        children = Node.get_children()
    except UaStatusCodeError:
        return None

    # BFS Search
    for child in children:
        # Catch bad node configuration
        try:
            if child.get_display_name().Text == prgName:
                return child
        except UaStatusCodeError:
            continue

    # nothing found -> look at each child
    for child in children:
        search_result = getPrgNode(child, prgName)
        if search_result is not None:
            return search_result

    return None


def getSubNode(prgNode, NodeName):
    """ Find Sub-Node in Programm Node

    Arguments:
        prgNode {ua PrgNode} -- Programm node to scan
        NodeName {[type]} -- Name of Sub-Node to find

    Returns:
        ua Node -- Sub-Node
    """
    for child in prgNode.get_children():
        if child.get_display_name().Text == NodeName:
            return child


def maintainConnection(aliveNode, endNode, endToggleNode):
    if endNode.get_value():
        # reset button on PLC
        endToggleNode.set_value(DV_FALSE)
        # end Simulation loop
        return False
    else:  # maintain connection
        if not aliveNode.get_value():
            aliveNode.set_value(DV_TRUE)
        return True

from jnpr.junos import Device
from lxml import etree
from jnpr.junos import exception
import pprint
from jnpr.junos.utils.config import Config
import ipaddress
import time

pp = pprint.PrettyPrinter(indent=4)


key_list = ['input-errors',
            'input-drops',
            'framing-errors',
            'input-runts',
            'input-discards',
            'input-l3-incompletes',
            'input-l2-channel-errors',
            'input-l2-mismatch-timeouts'
            'input-fifo-errors',
            'input-resource-errors',
            'carrier-transitions',
            'output-errors',
            'output-collisions',
            'output-drops',
            'aged-packets',
            'mtu-errors',
            'hs-link-crc-errors',
            'output-fifo-errors',
            'output-resource-errors']


def main():
    """Main Function."""
    global dev
    global interface

    router_id, interface = check_task()

    dev = Device(host='192.168.122.4', user='lab', password='abc123')

    dev.open()

    ip_address, loopback = get_config(interface)
    cur_if, hw_mac, cur_loopback  = get_if_info(interface)

    other_ip = get_other_ip(ip_address)
    set_config(interface, ip_address, other_ip, hw_mac)
    
    #script sleep just for testing purpose, please remove in production.
    time.sleep(60)
    result = dev.rpc.ping(host=other_ip, count='5', bypass_routing=True)

    pp.pprint(etree.dump(result))
    remove_config(interface, ip_address, other_ip, hw_mac)


def check_task():
    """Check available task."""
    # sql = ("SELECT * FROM phy_int INNER JOIN router"
    #        "on router.id=phy_in.router_id"
    #        "where phy_int.started=0")
    # cursor.execute(sql)
    # result = cursor.fectchone()
    router_id = 1
    if_name = "ge-0/0/0"

    return router_id, if_name


def get_config(interface):
    data = dev.rpc.get_config(filter_xml='<interfaces></interfaces>')
    #pp.pprint(etree.dump(data))
    match_if = './/interface[name="{}"]'.format(interface)

    match = data.find(match_if)
    ip_address = match.findtext('.//family/inet/address/name')

    loopback = match.find('.//gigether-options/loopback')

    if match.find('.//gigether-options/loopback') is not None:
        loopback = True
    else:
        loopback = False

    return ip_address, loopback


def get_other_ip(ip_address):
    """Get other ip address."""
    host4 = ipaddress.ip_interface(unicode(ip_address, "utf-8"))
    for ip in host4.network.hosts():
        if str(ip) != ip_address.split("/")[0]:
            return str(ip)


def set_config(*args):
    """"Set configuration."""
    with Config(dev, mode='private') as cu:
        lo_command = ("set interfaces {} "
                      "gigether-options loopback"
                      .format(args[0]))

        mac_command = ("set interfaces {} "
                       "unit 0 family inet "
                       "address {} arp {} mac {}"
                       .format(args[0],
                               args[1],
                               args[2],
                               args[3]))

        cu.load(lo_command, format='set')
        print(mac_command)
        cu.load(mac_command, format='set')

        print(cu.pdiff())
        cu.commit()


def remove_config(*args):
    """"remove configuration."""
    with Config(dev, mode='private') as cu:
        lo_command = ("delete interfaces {} "
                      "gigether-options loopback"
                      .format(args[0]))

        mac_command = ("delete interfaces {} "
                       "unit 0 family inet "
                       "address {} arp {} mac {}"
                       .format(args[0],
                               args[1],
                               args[2],
                               args[3]))

        cu.load(lo_command, format='set')
        cu.load(mac_command, format='set')
        cu.commit()


def get_if_info(interface):
    if_info = {}
    data = dev.rpc.get_interface_information(interface_name=interface, normalize=True)
    #print(etree.dump(data))
    print(data.text)
    if_name = data.findtext('.//name')
    loopback = data.findtext('.//loopback')
    mac_address = data.findtext('.//hardware-physical-address')
    ip_address = data.findtext('.//ifa-local')
    ifa_destination = data.findtext('.//ifa-destination')
    print(if_name, loopback, mac_address)
    return if_name, mac_address, loopback

def clear_statistic(interface):
    dev.rpc.clear_interfaces_statistics(interface_name=interface)


def get_if_errors():
    if_errors = {}
    data = dev.rpc.get_interface_information(extensive=True, normalize=True)
    for item in key_list:
        tag = './/' + item
        text = data.findtext(tag)
        print(item, text)
        if_errors[item] = text
    return if_errors


if __name__ == "__main__":
    main()

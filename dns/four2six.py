#!/usr/bin/env python3


from subprocess import check_output
from json import dumps
from ipaddress import IPv4Address, IPv6Address

from config import *

def scd_mapped_ipv4v6(ip4, ip6_subnet_prefix):
    ip6 = [int(o) for o in str(ip4).split('.')]
    if len(ip6) == 4:
        ip6 = ip6_subnet_prefix + ('::%02x%02x:%02x%02x' % tuple(ip6))
        return IPv6Address(ip6)
    return None


def process_zone(zone, f_fwd, f_rev):
    for r in zone:
        if len(r) == 5:
            z_name, z_ttl, z_class, z_type, z_ip4 = r
            if z_type == 'A' and z_class == 'IN':
                ip4 = IPv4Address(z_ip4)

                subnet_prefix = None

                for subnet, realm in SUBNETS_IPV4.items():
                    if ip4 in subnet:
                        subnet_prefix = SUBNET_PREFIXES[realm]

                if subnet_prefix:
                    # resource record format : name, ttl, class, type, data
                    ip6 = scd_mapped_ipv4v6(ip4, subnet_prefix)
                    f_fwd.write('%s\t%s\tIN\tAAAA\t%s\n' % (z_name, z_ttl, ip6))

                    rev6 = ip6.reverse_pointer

                    f_rev.write('%s\t%s\tIN\tPTR\t%s\n' % (rev6, z_ttl, z_name))


def main():
    for domain in DOMAINS:
        zone = check_output(['dig', '@'+NAMESERVER, domain, 'axfr'])
        zone = zone.decode()
        zone = [l.strip().split() for l in zone.split(u'\n')]

        with open('%s.forward.zone' % domain, 'w') as f_fwd:
            with open('%s.reverse.zone' % domain, 'w') as f_rev:
                process_zone(zone, f_fwd, f_rev)


if __name__ == '__main__':
    main()


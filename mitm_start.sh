laniface="ppp0"
port="20755"

echo "Setting up default iptables policy"
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

echo "WARNING! Make sure your DNS resolver is correct. I am helpfully catting it for you now."
cat /etc/resolv.conf

echo "Enabling IP forwarding"
echo 1 > /proc/sys/net/ipv4/ip_forward

echo "Performing MITM on $laniface"
set -x
iptables -t nat -A PREROUTING -j REDIRECT -i $laniface -p tcp -m tcp --to-ports $port
#iptables -t nat -A PREROUTING -j REDIRECT -i $laniface -p udp -m udp --to-ports $port

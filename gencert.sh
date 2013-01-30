base="cert"
newcerts="$base/newcerts"
config="openssl.cnf"
domain=$1
subj=$2

if [ ! -e $newcerts ]; then
  mkdir -p $newcerts
fi

if [ -e $newcerts/$domain.pem ]; then
  exit
fi

if [ ! -e $base/serial ]; then
  echo 01 > $base/serial
fi

if [ ! -e $base/index.txt ]; then
  touch $base/index.txt
fi

if [ ! -e $base/ca.key ]; then
  openssl req -config openssl.cnf -new -x509 -extensions v3_ca -keyout $base/ca.key -out $base/ca.crt -days 3650 -nodes -subj '/CN=justtrustme.bro/O=Pyxie Trusted Packet Proxyz, Inc./C=US/ST=CA/L=San Francisco/emailAddress=gabe@isecpartners.com/'
fi

openssl req -new -nodes -outform PEM -keyout $newcerts/$domain.key -out $newcerts/$domain.csr -days 3650 -subj "$subj"
yes|openssl ca -md sha1 -config $config -policy policy_anything -out $newcerts/$domain.crt -infiles $newcerts/$domain.csr 
# shameless hack below
cat $newcerts/$domain.crt $newcerts/$domain.key |grep -A 1000 '-----BEGIN CERTIFICATE-----' > $newcerts/$domain.pem
rm $newcerts/$domain.csr $newcerts/$domain.key $newcerts/$domain.crt

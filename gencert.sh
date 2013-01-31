base="cert"
newcerts="$base/newcerts"
config="openssl.cnf"
domain=$1
subj=$2

if [ -z "$domain" ]; then
  echo "Usage: $0 <domain> [subject]"
  exit 0
fi

if [ -z "$subj" ]; then
  subj="/CN=$domain/O=$domain, Inc./"
fi

if [ ! -e "$newcerts" ]; then
  mkdir -p $newcerts
fi

if [ -e "$newcerts/$domain.pem" ]; then
  exit
fi

if [ ! -e $base/serial ] || [ ! -e $base/index.txt ]; then
  rm -f $base/index.txt $base/serial
  touch $base/index.txt
  echo 01 > $base/serial
fi

if [ ! -e $base/ca.key ]; then
  openssl req -config openssl.cnf -new -x509 -extensions v3_ca -keyout $base/ca.key -out $base/ca.crt -days 3650 -nodes -subj '/CN=justtrustme.bro/O=Pyxie Trusted Packet Proxyz, Inc./C=US/ST=CA/L=San Francisco/emailAddress=gabe@isecpartners.com/'
fi

openssl req -new -nodes -outform PEM -keyout "$newcerts/$domain.key" -out "$newcerts/$domain.csr" -days 3650 -subj "$subj"
openssl ca -startdate 130101120000Z -enddate 330101000000Z -md sha1 -config $config -policy policy_anything -notext -batch -out "$newcerts/$domain.crt" -infiles "$newcerts/$domain.csr"
cat "$newcerts/$domain.key" "$newcerts/$domain.crt" "$base/ca.crt" >> "$newcerts/$domain.pem"
rm "$newcerts/$domain.csr" "$newcerts/$domain.key" "$newcerts/$domain.crt"

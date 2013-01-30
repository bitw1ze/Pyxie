base="cert"
newcerts="$base/newcerts"
config="openssl.cnf"
domain=$1
subj=$2

if [ -e $newcerts/$domain ]; then
  exit
fi

if [ ! -e $base/serial ]; then
  echo 01 > serial
fi

if [ ! -e $base/index.txt ]; then
  touch $base/index.txt
fi

openssl req -new -nodes -outform PEM -keyout $newcerts/$domain.key -out $newcerts/$domain.csr -days 3650 -subj "$subj"
yes|openssl ca -md sha1 -config $config -policy policy_anything -out $newcerts/$domain.crt -infiles $newcerts/$domain.csr 
cat $newcerts/$domain.crt $newcerts/$domain.key > $newcerts/$domain.pem
rm $newcerts/$domain.csr $newcerts/$domain.key $newcerts/$domain.crt

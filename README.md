## Script for requesting certificate (AWS ACM)


### Sript arguments
| Name                 | Description    | Default   |                               
| ------------------- | ---------------|------------|
| `--profile`           | AWS_PROFILE  | default|
| `--method`           | Validation method | DNS|
| `--accelerator_ips`           | Ips of AWS Gloval Accelerator to route traffic on it | 213.110.148.240 213.110.148.241|
| `--domain_name`           | Specifies the domain validation method DNS or EMAIL | |
| `--customer_email`           | Customer email | |
| `--mail_from`           | Mail from | support@gmail.com|
| `--mail_cc`           |Mail cc | tec@gmail.com|
| `--wildcard`           | Request Wildcard certificate| False|
| `--with_wildcard`           | Request client certificate with wildcard| False|
| `--alternative_names`           | Additional FQDNs to be included in the Subject Alternative Name | |
| `--smtp_user`           | SMTP user | none |
| `--smtp_pas`           | SMTP password | none |
| `--smtp_host`           | SMTP host | none |
| `--smtp_port`           | SMTP server port | none |


### Please be informed that you should put into examples next arguments
```sh
--smtp_user {} --smtp_pass {} --smtp_host {} --smtp_port {} --mail_cc {} --mail_from 
```

## To request client certificate

```sh
python3 request_certificate.py --domain_name roslyakov.net --customer_email ei.roslyakov@gmail.com
```

## To request client certificate with wildcard
```
python3 request_certificate.py --domain_name roslyakov.net --with_wildcard --customer_email ei.roslyakov@gmail.com
```

## To request wildcard client certificate (*.roslyakov.net)
```sh
python3 request_certificate.py --domain_name roslyakov.net --wildcard --customer_email ei.roslyakov@gmail.com
```

## To request client certificate with alternative_names 
```sh
python3 request_certificate.py --domain_name ni.roslyakov.net --alternative_names three.roslyakov.net --customer_email ei.roslyakov@gmail.com
```


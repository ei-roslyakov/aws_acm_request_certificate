import argparse
import time

import boto3

import smtplib

import loguru

from terminaltables import AsciiTable


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = loguru.logger


def acm_client(profile):
    session = boto3.Session(profile_name=profile)
    client = session.client("acm")

    return client


def argument_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--profile",
        "-p",
        required=False,
        type=str,
        default="default",
        action="store",
        help="AWS Profile"
    )
    parser.add_argument(
        "--method",
        "-m",
        required=False,
        type=str,
        default="DNS",
        action="store",
        help="Validation method"
    )
    parser.add_argument(
        "--accelerator_ips",
        required=False,
        type=str,
        default="213.110.148.240\n213.110.148.241",
        action="store",
        help="Ips of AWS Gloval Accelerator to route traffic on it"
    )
    parser.add_argument(
        "--domain_name",
        "-d",
        required=False,
        type=str,
        action="store",
        help="Specifies the domain name"
    )
    parser.add_argument(
        "--customer_email",
        required=False,
        type=str,
        action="store",
        help="Customer email"
    )
    parser.add_argument(
        "--mail_from",
        required=False,
        type=str,
        action="store",
        help="Mail from"
    )
    parser.add_argument(
        "--mail_cc",
        required=False,
        type=str,
        action="store",
        help="Mail cc"
    )
    parser.add_argument(
        "--wildcard",
        required=False,
        default=False,
        action="store_true",
        help="Request wildcard certificate")
    parser.add_argument(
        "--with_wildcard",
        required=False,
        default=False,
        action="store_true",
        help="Request certificate for domain and domain with wildcard")
    parser.add_argument(
        "--alternative_names",
        "-a",
        nargs="+",
        type=str,
        required=False,
        action="store",
        help="Additional FQDNs to be included in the Subject Alternative Name"
    )
    parser.add_argument(
        "--smtp_user",
        type=str,
        required=False,
        action="store",
        help="SMTP user"
    )
    parser.add_argument(
        "--smtp_pass",
        type=str,
        required=False,
        action="store",
        help="SMTP password"
    )
    parser.add_argument(
        "--smtp_host",
        type=str,
        required=False,
        action="store",
        help="SMTP host"
    )
    parser.add_argument(
        "--smtp_port",
        type=str,
        required=False,
        action="store",
        help="SMTP server port"
    )

    return parser.parse_args()


def request_certificate(client, domain_name, alternative_names, method, wildcard, with_wildcard):

    try:
        if with_wildcard:
            response = client.request_certificate(
                DomainName=domain_name,
                ValidationMethod=method,
                SubjectAlternativeNames=[f"*.{domain_name}"],
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"{domain_name}-cert"
                    },
                ]
            )
            logger.info("Certificate was requested")
            logger.info(f"Certificate ard: {response['CertificateArn']}")
            return response["CertificateArn"]
        if alternative_names:
            response = client.request_certificate(
                DomainName=domain_name,
                ValidationMethod=method,
                SubjectAlternativeNames=[domain for domain in alternative_names],
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"{domain_name}-cert"
                    },
                ]
            )
            logger.info("Certificate was requested")
            logger.info(f"Certificate ard: {response['CertificateArn']}")
            return response["CertificateArn"]
        
        if wildcard:
            response = client.request_certificate(
                DomainName=f"*.{domain_name}",
                ValidationMethod=method,
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"{domain_name}-cert"
                    },
                ]
            )
            logger.info("Certificate was requested")
            logger.info(f"Certificate ard: {response['CertificateArn']}")
            return response["CertificateArn"]

        if not alternative_names:
            response = client.request_certificate(
                DomainName=domain_name,
                ValidationMethod=method,
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"{domain_name}-cert"
                    },
                ]
            )
            logger.info("Certificate was requested")
            logger.info(f"Certificate ard: {response['CertificateArn']}")
            return response["CertificateArn"]
        

    except Exception as e:
        logger.exception(f"Something went wrong {e}")
        raise


def get_validation_data(client, certificate_arn):
    logger.info(f"Getting data about {certificate_arn} certificate")
    try:
        should_wait = True
        while should_wait:
            response = client.describe_certificate(
                CertificateArn=certificate_arn
            )
            if "DomainValidationOptions" in response["Certificate"]:
                if "ResourceRecord" in response["Certificate"]["DomainValidationOptions"][-1]:
                    should_wait = False
                    logger.debug(f"CNAMEs were created")
                    break
            time.sleep(2)

            logger.debug(f"There are not ResourceRecord in response")

        header = ["Record Name", "Record Type", "Record value"]
        data = [header]

        try:
            validation_data = [x["ResourceRecord"] for x in response["Certificate"]["DomainValidationOptions"]]
            for record in validation_data:
                data_to_append = [record["Name"], record["Type"], record["Value"]]
                data.append(data_to_append)
        except Exception as e:
            logger.exception(f"Something went wrong {e}")

        table = AsciiTable(data)
        table.inner_row_border = True
        logger.info(f"Validation data")
        print(table.table)

        return table.table

    except Exception as e:
        logger.exception(f"Something went wrong with getting validation data {e}")
        raise


def make_email_template(domains, records_for_validate, ga_ips, wildcard):

    header = ["Record Name", "Record Type", "Record value"]
    data = [header]

    for domain in domains:
        if wildcard:
            data_to_append = [f"some_domain.{domain}", "A", ga_ips]
            data.append(data_to_append)
            break

        data_to_append = [domain, "A", ga_ips]
        data.append(data_to_append)
    table = AsciiTable(data)
    table.inner_row_border = True
    routing_records = table.table

    MESSAGE_TEMPLATE = f"""
Hi there.\n
You have configured your own domain for our organisation.\n
For routing traffic from your domains, please create the following DNS records:\n
{routing_records}\n\n
We have requested SSL certificate for these domains. For validation them, please create the following DNS records:\n
{records_for_validate}\n
You can find instructions in attachment.\n\n
Best regards,
Rosliakov.
"""

    return f"""<html>
            <head></head>
            <body>
              <pre>{MESSAGE_TEMPLATE}</pre>
            </body>
            </html>
        """


def send_mail_to_recipient(server, message, ms_from, ms_to, ms_cc):
    msg = MIMEMultipart()

    msg["From"] = ms_from
    msg["Subject"] = "Sphere traffic routing"
    msg["CC"] = ms_cc
    msg.attach(MIMEText(message, "html"))

    try:
        pdf = MIMEApplication(open("how_to_create_dns_record.pdf", "rb").read())
        pdf.add_header("Content-Disposition", "attachment", filename=str("how_to_create_dns_record.pdf"))
        msg.attach(pdf)
    except FileNotFoundError as e:
        logger.exception(f"File does not exist: '{e}'")
        raise
    except Exception as e:
        logger.exception(f"Something went wrong {e}")
        raise

    server.sendmail(msg["From"], [ms_to, ms_cc], msg.as_string())
    logger.info("Mail was delivered")


def main():
    logger.info("Application started")
    args = argument_parser()

    USERNAME = args.smtp_user
    PASSWORD = args.smtp_pass
    SMTP_SERVER = args.smtp_host
    SERVER_PORT = args.smtp_port

    client = acm_client(args.profile)
    certificate = request_certificate(client, args.domain_name, args.alternative_names, args.method, args.wildcard, args.with_wildcard)
    validation_data = get_validation_data(client, certificate)
    domais_list = []

    try:
        domais_list.append(args.domain_name)
        if args.alternative_names:
            domais_list = domais_list + args.alternative_names
    except Exception as e:
        logger.exception(f"Something went wrong {e}")
        raise

    logger.info(f"Domains: {domais_list}")
    message = make_email_template(
        domais_list,
        validation_data,
        args.accelerator_ips,
        args.wildcard
    )

    server = smtplib.SMTP(f"{SMTP_SERVER}:{SERVER_PORT}")
    server.starttls()
    server.login(USERNAME, PASSWORD)

    try:
        send_mail_to_recipient(server, message, args.mail_from, args.customer_email, args.mail_cc)
    except BaseException as e:
        logger.exception("error sending message: '{}'".format(e))

    finally:
        server.quit()

    logger.info("Application finished")

    return 0


if __name__ == "__main__":
    res = main()
    exit(res)

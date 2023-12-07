import json
import boto3
import os

client = boto3.client('ses')
lam = boto3.client('lambda')
turn_on_email_notification = os.environ['turn_on_email_notification']
source_sender = os.environ['source_sender']

def send_email(content, recipients):
    response = client.send_email(
        Destination={
            'ToAddresses': recipients
        },
        Message={
            'Body': {
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': f"""
            Hi there, 
                
            Comes with the meeting minutes you just requested to transcribe and summary. Please check. Thanks.
            ============================================================================
                
            {content}
                
            """,
                }
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': '[Notification] Meeting Minutes Summary',
            },
        },
        Source=source_sender
    )

    print(response)
    print("Email Sent Successfully. MessageId is: " + response['MessageId'])

    return response


def lambda_handler(event, context):
    resp = {'status': False, 'TotalItems': {}, 'Items': []}

    if not 'Records' in event:
        resp = {'status': False, "error_message": 'No Records found in Event'}
        return resp

    print(f"Event:{event}")

    for r in event.get('Records'):

        # For UPDATE
        if r.get('eventName') == "MODIFY":

            if turn_on_email_notification == "true" or turn_on_email_notification == "True":
                _datetime = r['dynamodb']['NewImage']['datetime']['S']
                _summary = r['dynamodb']['NewImage']['summary']['S']
                _recipients = r['dynamodb']['NewImage']['recipients']['S']

                _content = f"""
                Request time: {_datetime}
                
                Summary: 
                {_summary}
                """

                print(f"Formatted Content: {_content}")
                print("Sending email notification.")

                response = send_email(_content, [x.strip() for x in _recipients.split(',')])

                print(f"resp:{response}")

            else:
                print("Email Notification Disabled. Please confirm if SES is setup before enabling.")

        # For INSERT
        # should trigger 
        if r.get('eventName') == "INSERT":
            print("Invoke auto summary.")

            lam.invoke(
                FunctionName=os.environ['asr_content_processor_func_name'],
                InvocationType="Event",
                Payload=json.dumps(event)
            )

            response = "Triggered auto summary."

            print(response)

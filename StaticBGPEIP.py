# -*- coding: UTF-8 -*-

import sys, boto3

VPC = 'vpc-xxxxxxxxxxxxxxx';
EC2TAG = 'isChangeEIP';

def change():
    batchID = sys.argv[2];
    ec2Client = boto3.client('ec2');

    ec2Response = ec2Client.describe_instances(
        Filters=[
            {
                'Name': 'tag-key',
                'Values': [
                    EC2TAG,
                ]
            }
        ],
        MaxResults=999
    )

    for i in range(len(ec2Response['Reservations'])):
        for j in range(len(ec2Response['Reservations'][i]['Instances'])):
            publicIpAddress = ec2Response['Reservations'][i]['Instances'][j].get('PublicIpAddress');

            if publicIpAddress != None:
                try:
                    addressResponse = ec2Client.describe_addresses(PublicIps=[publicIpAddress]);
                    associationId = addressResponse['Addresses'][0]['AssociationId'];
                    ec2Client.disassociate_address(AssociationId=associationId);
                except Exception as e:
                    pass

            eipResponse = ec2Client.allocate_address(Domain=VPC, PublicIpv4Pool='xxx-staticbgp', TagSpecifications=[{'ResourceType':'elastic-ip', 'Tags': [{'Key': 'batchID', 'Value': batchID}]}]);

            ec2Client.associate_address(InstanceId=ec2Response['Reservations'][i]['Instances'][j]['InstanceId'], AllocationId=eipResponse['AllocationId']);

def rollback():
    batchID = sys.argv[2];
    ec2Client = boto3.client('ec2');

    ec2Response = ec2Client.describe_instances(
        Filters=[
            {
                'Name': 'tag-key',
                'Values': [
                    EC2TAG,
                ]
            }
        ],
        MaxResults=999
    )

    oldEIPResponse = ec2Client.describe_addresses(Filters=[{'Name': 'tag:batchID','Values': [batchID]}]);
    
    if len(oldEIPResponse['Addresses']) == 0:
        sys.exit(0);

    m = 0;
    for i in range(len(ec2Response['Reservations'])):
        for j in range(len(ec2Response['Reservations'][i]['Instances'])):
            publicIpAddress = ec2Response['Reservations'][i]['Instances'][j].get('PublicIpAddress');

            if publicIpAddress != None:
                try:
                    addressResponse = ec2Client.describe_addresses(PublicIps=[publicIpAddress]);
                    associationId = addressResponse['Addresses'][0]['AssociationId'];
                    ec2Client.disassociate_address(AssociationId=associationId);
                except Exception as e:
                    pass
            try:
                ec2Client.associate_address(InstanceId=ec2Response['Reservations'][i]['Instances'][j]['InstanceId'], AllocationId=oldEIPResponse['Addresses'][m]['AllocationId']);
                m = m + 1;
            except Exception as e:
                pass
   
def delete():
    print ('Delete EIP Begin');
    batchID = sys.argv[2];
    ec2Client = boto3.client('ec2');

    oldEIPResponse = ec2Client.describe_addresses(Filters=[{'Name': 'tag:batchID','Values': [batchID]}]);

    for index in range(len(oldEIPResponse['Addresses'])):
        ec2Client.release_address(AllocationId=oldEIPResponse['Addresses'][index]['AllocationId']);
    print ('Delete EIP Finsh');

if __name__ == "__main__":
    if 'change' == sys.argv[1]:
        if len(sys.argv) != 3:
            print ('参数数量不正确，请输入正确的参数！');
            sys.exit(0);
        change();
    elif 'rollback' == sys.argv[1]:
        if len(sys.argv) != 3:
            print ('参数数量不正确，请输入正确的参数！');
            sys.exit(0);
        rollback();
    elif 'delete' == sys.argv[1]:
        if len(sys.argv) != 3:
            print ('参数数量不正确，请输入正确的参数！');
            sys.exit(0);
        delete();
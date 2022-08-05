![status: inactive](https://img.shields.io/badge/status-inactive-red.svg)

This project is no longer actively developed or maintained.

# **Active Directory User Management API**

## **Overview**

This project aims to provide a simple HTTP-based interface to ldap interactions with Microsoft Active Directory. It is designed to sit behind Google Identity-Aware Proxy as a bridge between Google Cloud service account identities and Active Directory administration.

Internally this project utilizes both python-ldap and ldap3. Because python-ldap wraps OpenLDAP, it has robust support for GSSAPI integrity and confidentiality which are required for exchanging secrets with some Active Directory configurations. ldap3 on the other hand provides Active Directory schema awareness and data type handling.

## **Setup**

* Enable Google Cloud Platform APIs:
  ```
  gcloud services enable compute.googleapis.com
  gcloud services enable cloudkms.googleapis.com
  gcloud services enable iap.googleapis.com
  ```
* Initialize AppEngine to your selected region. Please note that AppEngine region selection is project-wide and cannot be changed. Also, us-central1 and europe-west1  are referred to as us-central and europe-west in the context of AppEngine. For more information, see [App Engine Locations](https://cloud.google.com/appengine/docs/locations).
  ```
  REGION=us-central
  gcloud app create --region $REGION
  ```
* Configure Identity-Aware Proxy
  * Navigate to ```≡ > Security > Identity-Aware Proxy```
  * Click ```CONFIGURE CONSENT SCREEN```
  * Select ```External``` and click ```CREATE```
  * Enter an ```App name``` such as ```Active Directory User Management API```
  * Enter a ```User support email```. Consider using a group email alias.
  * Enter another email address under ```Developer contact information```. Again, consider using a group alias.
  * Click ```SAVE AND CONTINUE```.
  * On the ```Scopes``` page click ```SAVE AND CONTINUE```.
  * On the ```Test users``` page click ```SAVE AND CONTINUE```.
  * On the ```Summary``` page click ```BACK TO DASHBOARD```.
  * On the ```OAuth consent screen``` dashboard under ```Publishing status``` click ```PUBLISH APP```.
  * In the ```Push to production?``` dialog, click ```CONFIRM```.
  * Deploy dummy AppEngine sercvice to allow enabling IAP.
    * In Cloud Shell or similar environment, create a dummy app.yaml file and deploy default service with gcloud:\
      ```
      echo "runtime: python38" > app.yaml
      gcloud app deploy
      ```
      Answer "y" when prompted.
  * Navigate back to ```≡ > Security > Identity-Aware Proxy```. You should now see the AppEngine default service listed under ```HTTPS RESOURCES```.
  * Under ```All Web Services > App Engine app``` toggle the switch in the ```IAP``` column to enable IAP.
  * In the ```Turn on IAP``` dialog, click ```TURN ON```.
  * You should see ```OK``` in the ```Status``` column and at this point your App Engine app will only be accessible to identities you configure by selecting a resource and adding members to the ```Cloud IAP > IAP-secured Web App User``` role.
* Create KMS resources and grant permissions to AppEngine service account. You can utilize environment variables defined in app.yaml to configure different KMS resource identifiers if you choose:
  ```
  PROJECT=your-project-id-goes-here
  gcloud kms keyrings create active-directory-user-management-api --location global
  gcloud kms keyrings add-iam-policy-binding active-directory-user-management-api --location global --member serviceAccount:$PROJECT@appspot.gserviceaccount.com --role roles/cloudkms.cryptoKeyEncrypterDecrypter
  gcloud kms keys create ldap-bind-secrets --keyring active-directory-user-management-api --location global --purpose encryption
  ```
* Configure app.yaml, e.g.:
  * Add [network settings](https://cloud.google.com/appengine/docs/flexible/python/reference/app-yaml#network_settings) to specify a non-default or shared VPC for deployment of AppEngine instances. The specified VPC ("default" if unspecified) must have connectivity and name resolution to your Active Directory domain.
  * Adjust [service scaling settings](https://cloud.google.com/appengine/docs/flexible/python/reference/app-yaml#services) appropriately especially for a production deployment.
* Deploy AppEngine app:
  ```
  cd api/python
  gcloud app deploy
  ```

## **Usage**

**Service endpoint:** The service endpoint is your 
App Engine enpoint and API version such as ```https://{project}.uc.r.appspot.com/alpha```.\
**Path parameters:**

Parameter|Description
:---|:---
```project```|```string``` Project ID for this request.


## **Method:** connections.list
**HTTP request:** ```GET /connections``` \
**Path parameters:** None \
**Query parameters:** None \
**Request body:** The request body must be empty. \
**Response body:** If successful, the response body contains data with the following structure:
```
[{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}]
```

Field|Description
:---|:---
```[]```|```object``` A list of connection resources.
```[].name```|```string``` Name of the resource. Provided by the client when the resource is created.
```[].ldapUrl```|```string``` URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```[].credentials.user```|```string``` The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```[].credentials.password```|```string``` The password for binding to LDAP. This field will be masked in the response.


## **Method:** connections.insert
HTTP Request: ```POST /connections```\
**Path parameters:**\
None\
**Query parameters:**\
None\
**Request body:**\
The request body contains data with the following structure:
```
{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}
```

Field|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.
```ldapUrl```|```string``` URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```credentials.user```|```string``` The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```credentials.password```|```string``` The password for binding to LDAP. This field will be masked in the response.

**Response body:**\
If successful, the response body contains data with the following structure:
```
{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}
```

Field|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.
```ldapUrl```|```string``` URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```credentials.user```|```string``` The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```credentials.password```|```string``` The password for binding to LDAP. This field will be masked in the response.


## **Method:** connections.get
HTTP Request: ```GET /connections/{name}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.

**Query parameters:**\
None\
**Request body:**\
The request body must be empty.\
**Response body:**\
If successful, the response body contains data with the following structure:
```
{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}
```

Field|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.
```ldapUrl```|```string``` URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```credentials.user```|```string``` The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```credentials.password```|```string``` The password for binding to LDAP. This field will be masked in the response.


## **Method:** connections.delete
HTTP Request: ```DELETE /connections/{name}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.


**Query parameters:**\
None\
**Request body:**\
The request body must be empty.\
**Response body:**\
If successful, the response body contains data with the following structure:
```
{}
```


## **Method:** connections.update
HTTP Request: ```PUT /connections/{name}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.

**Query parameters:**\
None\
**Request body:**\
The request body contains data with the following structure:
```
{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}
```

Field|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.
```ldapUrl```|```string``` URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```credentials.user```|```string``` The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```credentials.password```|```string``` The password for binding to LDAP. This field will be masked in the response.

**Response body:**\
If successful, the response body contains data with the following structure:
```
{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}
```

Field|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.
```ldapUrl```|```string``` URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```credentials.user```|```string``` The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```credentials.password```|```string``` The password for binding to LDAP. This field will be masked in the response.

## Method: connections.patch
HTTP Request: ```PATCH /connections/{name}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.

**Query parameters:**\
None\
**Request body:**\
The request body contains data with the following structure:
```
{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}
```

Field|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.
```ldapUrl```|```string``` (Optional) URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```credentials.user```|```string``` (Optional) The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```credentials.password```|```string``` (Optional) The password for binding to LDAP. This field will be masked in the response.

**Response body:**\
If successful, the response body contains data with the following structure:
```
{
  "name": string,
  "ldapUrl": string,
  "credentials": {
    "user": string,
    "password": string
  }
}
```

Field|Description
:---|:---
```name```|```string``` Name of the resource. Provided by the client when the resource is created.
```ldapUrl```|```string``` URL for connecting to ldap. This should point to a specific domain controller not the domain itself, e.g. ```ldap://dc-1.example.com```..
```credentials.user```|```string``` The user for binding to LDAP. The current implementation uses kerberos and the user should be specified in the format of ```user@REALM``` where ```REALM``` is the domain name in all caps, e.g. ```user@EXAMPLE.COM```.
```credentials.password```|```string``` The password for binding to LDAP. This field will be masked in the response.

## **Method:** ldap.get
HTTP Request: ```GET /connections/{name}/ldap/{base}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the connection resource.
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DC=example,DC=com```.

**Query parameters:**

Parameter|Description
:---|:---
```scope```|```enum``` (Optional) Scope of the LDAP search. ```base``` to search the object itself, ```one``` to search the object’s immediate children, or ```sub``` to search the object and all its descendants. Default: ```sub```
```filter```|```string``` (Optional) A valid LDAP filter expression. See [LDAP Filters](https://ldap.com/ldap-filters/) for more information..
```attributes```|```string``` (Optional) Comma-delimited list of attribute names to include in response. Default: ```*```.

**Request body:**\
The request body must be empty.\
**Response body:**\
If successful, the response body contains data with the following structure:
```
[{
  "dn": string,
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}]
```

Field|Description
:---|:---
```[].dn```|```string``` Distinguished name of the entity.
```[].attributes.name```|```string``` Attribute name.
```[].attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

## **Method:** ldap.insert
HTTP Request: ```GET /connections/{name}/ldap/{base}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the connection resource.
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DC=example,DC=com```.

**Query parameters:**

Parameter|Description
:---|:---
```scope```|```enum``` (Optional) Scope of the LDAP search. ```base``` to search the object itself, ```one``` to search the object’s immediate children, or ```sub``` to search the object and all its descendants. Default: ```sub```
```filter```|```string``` (Optional) A valid LDAP filter expression. See [LDAP Filters](https://ldap.com/ldap-filters/) for more information..
```attributes```|```string``` (Optional) Comma-delimited list of attribute names to include in response. Default: ```*```.

**Request body:**\
The request body must be empty.\
**Response body:**\
If successful, the response body contains data with the following structure:
```
[{
  "dn": string,
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}]
```

Field|Description
:---|:---
```[].dn```|```string``` Distinguished name of the entity.
```[].attributes.name```|```string``` Attribute name.
```[].attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

## **Method:** ldap.delete
HTTP Request: ```DELETE /connections/{name}/ldap/{base}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the connection resource.
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DC=example,DC=com```.

**Query parameters:**

Parameter|Description
:---|:---
```scope```|```enum``` (Optional) Scope of the LDAP search. ```base``` to search the object itself, ```one``` to search the object’s immediate children, or ```sub``` to search the object and all its descendants. Default: ```sub```
```filter```|```string``` (Optional) A valid LDAP filter expression. See [LDAP Filters](https://ldap.com/ldap-filters/) for more information..

**Request body:**\
The request body must be empty.\
**Response body:**\
If successful, the response body contains data with the following structure:
```
{}
```

## **Method:** ldap.insert
HTTP Request: ```POST /connections/{name}/ldap/{base}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the connection resource.
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DC=example,DC=com```.

**Query parameters:**

Parameter|Description
:---|:---
```scope```|```enum``` (Optional) Scope of the LDAP search. ```base``` to search the object itself, ```one``` to search the object’s immediate children, or ```sub``` to search the object and all its descendants. Default: ```sub```
```filter```|```string``` (Optional) A valid LDAP filter expression. See [LDAP Filters](https://ldap.com/ldap-filters/) for more information..
```attributes```|```string``` (Optional) Comma-delimited list of attribute names to include in response. Default: ```*```.

**Request body:**\
The request body contains data with the following structure:
```
{
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}
```

Field|Description
:---|:---
```attributes.name```|```string``` Attribute name.
```attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

**Response body:**\
If successful, the response body contains data with the following structure:
```
{
  "dn": string,
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}
```

Field|Description
:---|:---
```dn```|```string``` Distinguished name of the entity.
```attributes.name```|```string``` Attribute name.
```attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

## **Method:** ldap.update
HTTP Request: ```PUT /connections/{name}/ldap/{base}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the connection resource.
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DC=example,DC=com```.

**Query parameters:**

Parameter|Description
:---|:---
```scope```|```enum``` (Optional) Scope of the LDAP search. ```base``` to search the object itself, ```one``` to search the object’s immediate children, or ```sub``` to search the object and all its descendants. Default: ```sub```
```filter```|```string``` (Optional) A valid LDAP filter expression. See [LDAP Filters](https://ldap.com/ldap-filters/) for more information..
```attributes```|```string``` (Optional) Comma-delimited list of attribute names to include in response. Default: ```*```.

**Request body:**\
The request body contains data with the following structure:
```
{
  "dn": string,
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}
```

Field|Description
:---|:---
```dn```|```string``` Distinguished name of the entity.
```attributes.name```|```string``` Attribute name.
```attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

**Response body:**\
If successful, the response body contains data with the following structure:
```
{
  "dn": string,
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}
```

Field|Description
:---|:---
```dn```|```string``` Distinguished name of the entity.
```attributes.name```|```string``` Attribute name.
```attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

## **Method:** ldap.patch
HTTP Request: ```PATCH /connections/{name}/ldap/{base}```\
**Path parameters:**

Parameter|Description
:---|:---
```name```|```string``` Name of the connection resource.
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DC=example,DC=com```.

**Query parameters:**

Parameter|Description
:---|:---
```scope```|```enum``` (Optional) Scope of the LDAP search. ```base``` to search the object itself, ```one``` to search the object’s immediate children, or ```sub``` to search the object and all its descendants. Default: ```sub```
```filter```|```string``` (Optional) A valid LDAP filter expression. See [LDAP Filters](https://ldap.com/ldap-filters/) for more information..
```attributes```|```string``` (Optional) Comma-delimited list of attribute names to include in response. Default: ```*```.

**Request body:**\
The request body contains data with the following structure:
```
{
  "dn": string,
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}
```

Field|Description
:---|:---
```dn```|```string``` Distinguished name of the entity.
```attributes.name```|```string``` Attribute name.
```attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

**Response body:**\
If successful, the response body contains data with the following structure:
```
{
  "dn": string,
  "attributes": {
    "name-1": value-1,
    "name-2": value-2,
    "name-3": value-3,
    ...
    "name-n": value-n
  }
}
```

Field|Description
:---|:---
```dn```|```string``` Distinguished name of the entity.
```attributes.name```|```string``` Attribute name.
```attributes.value```|```string``` or ```list``` single- or multi-valued attribute value.

## **Examples**

The following examples use ```curl_auth.sh``` as an example client. You can adapt these to your language of choice as long as your language can send/receive JSON data via HTTPS and you pass an appropriate bearer tokenin the ```Authorization``` header.

### **Create a connection**

As a first step, you might create a ```connection``` resource to hold parameters related to your connection to Active Directory. Note, the ```ldapUrl``` should point to a specific domain controller and the ```user``` includes the domain name in caps as a kerberos realm.

```
$ ./curl_auth.sh 'https://your-app-123456.uc.r.appspot.com/alpha/connections' -X POST -H "Content-Type: application/json" -d '{"name": "test-cnxn-1", "ldapUrl": "ldap://dc-1.example.com", "credentials": {"user":"user@EXAMPLE.COM", "password":"ChangeMe!"}}'
```
You should see output similar to the following:
```
{
  "credentials": {
    "password": "******",
    "user": "user@EXAMPLE.COM"
  },
  "ldapUrl": "ldap://dc-1.example.com",
  "name": "test-cnxn-1"
}
```

### **Create a user**

The following command will create a user using the Active Directory connection parameters defined in the previous step. Note that mutating operations (POST, PUT, PATCH, DELETE) to the ldap endpoint expect the combination of base DN and query parameters (scope, filter, etc.) to yield a singular result. In this example ```scope=base``` is provided to identify the base DN as the point of insertion for the new user.

```
$ ./curl_auth.sh 'https://your-app-123456.uc.r.appspot.com/alpha/connections/test-cnxn-1/ldap/cn=Users,dc=example,dc=com?scope=base' -X POST -H "Content-Type: application/json" -d '{"attributes":{"cn":"test-user","samAccountName":"test-user","unicodepwd":"ChangeMe!","userAccountControl":512,"objectClass":"user"}}'     
```
You should see output similar to the following:
```
[                                                                               
  {                                                                             
    "attributes": {                                                             
      "accountExpires": "never",                                                
      "badPasswordTime": "1601-01-01T00:00:00+00:00",      
      "badPwdCount": 0,
      "cn": "test-user",                                                        
      "codePage": 0,                                                            
      "countryCode": 0,                                                         
      "dSCorePropagationData": [                                                
        "1601-01-01T00:00:00+00:00"                                             
      ],                                                                        
      "distinguishedName": "CN=test-user,CN=Users,DC=example,DC=com",           
      "instanceType": 4,                                                        
      "lastLogoff": "1601-01-01T00:00:00+00:00",                                
      "lastLogon": "1601-01-01T00:00:00+00:00",                                 
      "logonCount": 0,                                                          
      "name": "test-user",                                                      
      "objectCategory": "CN=Person,CN=Schema,CN=Configuration,DC=example,DC=com",                                                                               
      "objectClass": [                                                          
        "top",                                                                  
        "person", 
        "organizationalPerson", 
        "user"
      ], 
      "objectGUID": "{00b7ea38-db49-47e6-891c-51241a344bf5}", 
      "objectSid": "S-1-5-21-2817136910-1814725959-1657134757-1106", 
      "primaryGroupID": 513, 
      "pwdLastSet": "2021-03-07T03:26:49.943209+00:00", 
      "sAMAccountName": "test-user", 
      "sAMAccountType": 805306368, 
      "uSNChanged": 12950, 
      "uSNCreated": 12948, 
      "userAccountControl": 512, 
      "whenChanged": "2021-03-07T03:26:49+00:00", 
      "whenCreated": "2021-03-07T03:26:49+00:00"
    }, 
    "dn": "cn=test-user,cn=Users,dc=example,dc=com"
  }
]
```

### **Add user to group - step 1**

You can add a user to a group by appending the DN of the user to the list of
values stored with the group resource in the ```member``` multi-valued
attribute. The example below shows how to query for the group by specifying the
group's DN as the base DN of the ldap resource. Additionally the example shows
how to narrow results by only returning the resource's ```member``` attribute.
Other attributes could be added to the output by specfying a comma-delimtied
list of attribute names.

```
$ ./curl_auth.sh 'https://your-app-123456.uc.r.appspot.com/alpha/connections/test-cnxn-1/ldap/cn=Domain%20Admins,cn=Users,dc=example,dc=com?attributes=member'
```
You should see output similar to the following:
```
[
  {
    "attributes": {
      "member": [
        "CN=Administrator,CN=Users,DC=example,DC=com"
      ]
    }, 
    "dn": "CN=Domain Admins,CN=Users,DC=example,DC=com"
  }
]
```

### **Add user to group - step 2**
To modify group members, the PATCH method is used to update only the
```member``` attribute specifying the list retrieved in the previous step with
the new group member appended to the end of the list.

```
$ ./curl_auth.sh 'https://your-app-123456.uc.r.appspot.com/alpha/connections/test-cnxn-1/ldap/cn=Domain%20Admins,cn=Users,dc=example,dc=com?attributes=member&scope=base' -X PATCH -H "Content-Type: application/json" -d '{"attributes":{"member":["cn=Administrator,cn=Users,dc=example,dc=com","cn=test-user,cn=Users,dc=example,dc=com"]}}'
```
You should see output similar to the following:
```
[
  {
    "attributes": {
      "member": [
        "CN=test-user,CN=Users,DC=example,DC=com", 
        "CN=Administrator,CN=Users,DC=example,DC=com"
      ]
    }, 
    "dn": "cn=Domain Admins,cn=Users,dc=example,dc=com"
  }
]
```

### **Rename a user**
In this example, we use the PATCH operation to rename a user. The base DN
selects the user and the new name is specified with the ```cn``` attribute.
Notice that output is also limited to a list of attributes with a query
parameter.

```
$ ./curl_auth.sh 'https://your-app-123456.uc.r.appspot.com/alpha/connections/test-cnxn-1/ldap/cn=test-user,cn=Users,dc=example,dc=com?attributes=cn,sAMAccountName' -X PATCH -H "Content-Type: application/json" -d '{"attributes":{"cn":"new-name"}}'
```
You should see output similar to the following:
```
[
  {
    "attributes": {
      "cn": "new-name", 
      "sAMAccountName": "test-user"
    }, 
    "dn": "cn=new-name,cn=Users,dc=example,dc=com"
  }
]
```

### **Delete a user**
You can clean up by deleting this test user with its new DN and the DELETE
method.

```
$ ./curl_auth.sh 'https://your-app-123456.uc.r.appspot.com/alpha/connections/test-cnxn-1/ldap/cn=new-name,cn=Users,dc=example,dc=com' -X DELETE
```
You should see output similar to the following:
```
{}
```


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
App Engine enpoint and API version such as ```https://{project}.uc.r.appspot.com/v0beta1```.\
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
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DN=example,DN=com```.

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
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DN=example,DN=com```.

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
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DN=example,DN=com```.

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
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DN=example,DN=com```.

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
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DN=example,DN=com```.

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
```base```|```string``` Base DN from which to initiate LDAP search. Example: ```DN=example,DN=com```.

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


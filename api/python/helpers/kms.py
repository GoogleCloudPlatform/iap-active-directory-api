# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# modified from https://cloud.google.com/kms/docs/encrypt-decrypt

from google.cloud import kms
import base64
import crcmod
import six

# Create the client.
client = kms.KeyManagementServiceClient()

def encrypt_symmetric(project_id, location_id, key_ring_id, key_id, plaintext):
    """
    Encrypt plaintext using a symmetric key.

    Args:
        project_id (string): Google Cloud project ID (e.g. 'my-project').
        location_id (string): Cloud KMS location (e.g. 'us-east1').
        key_ring_id (string): ID of the Cloud KMS key ring (e.g. 'my-key-ring').
        key_id (string): ID of the key to use (e.g. 'my-key').
        plaintext (string): message to encrypt

    Returns:
        bytes: base 64 encoded cipher text

    """

    # Convert the plaintext to bytes.
    plaintext_bytes = plaintext.encode('utf-8')

    # Optional, but recommended: compute plaintext's CRC32C.
    # See crc32c() function defined below.
    plaintext_crc32c = crc32c(plaintext_bytes)

    # Build the key name.
    key_name = client.crypto_key_path(project_id, location_id, key_ring_id, key_id)

    # Call the API.
    encrypt_response = client.encrypt(
      request={'name': key_name, 'plaintext': plaintext_bytes, 'plaintext_crc32c': plaintext_crc32c})

    # Optional, but recommended: perform integrity verification on encrypt_response.
    # For more details on ensuring E2E in-transit integrity to and from Cloud KMS visit:
    # https://cloud.google.com/kms/docs/data-integrity-guidelines
    if not encrypt_response.verified_plaintext_crc32c:
        raise Exception('The request sent to the server was corrupted in-transit.')
    if not encrypt_response.ciphertext_crc32c == crc32c(encrypt_response.ciphertext):
        raise Exception('The response received from the server was corrupted in-transit.')
    # End integrity verification

#    print('Ciphertext: {}'.format(base64.b64encode(encrypt_response.ciphertext)))
#    return encrypt_response
    return base64.b64encode(encrypt_response.ciphertext)

def crc32c(data):
    """
    Calculates the CRC32C checksum of the provided data.

    Args:
        data: the bytes over which the checksum should be calculated.

    Returns:
        An int representing the CRC32C checksum of the provided bytes.
    """
    crc32c_fun = crcmod.predefined.mkPredefinedCrcFun('crc-32c')
    return crc32c_fun(six.ensure_binary(data))

def decrypt_symmetric(project_id, location_id, key_ring_id, key_id, ciphertext):
    """
    Decrypt the ciphertext using the symmetric key

    Args:
        project_id (string): Google Cloud project ID (e.g. 'my-project').
        location_id (string): Cloud KMS location (e.g. 'us-east1').
        key_ring_id (string): ID of the Cloud KMS key ring (e.g. 'my-key-ring').
        key_id (string): ID of the key to use (e.g. 'my-key').
        ciphertext (bytes): Encrypted bytes to decrypt.

    Returns:
        DecryptResponse: Response including plaintext.

    """

    data = base64.b64decode(ciphertext)

    # Build the key name.
    key_name = client.crypto_key_path(project_id, location_id, key_ring_id, key_id)

    # Call the API.
    decrypt_response = client.decrypt(request={'name': key_name, 'ciphertext': data})
#    print('Plaintext: {}'.format(decrypt_response.plaintext))
#    return decrypt_response
    return decrypt_response.plaintext.decode('utf-8')


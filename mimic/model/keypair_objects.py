"""
Keypair objects for mimic
"""

from characteristic import attributes

@attributes(['name', 'public_key', 'user_id'])
class KeyPair(object):
    """
    A KeyPair object
    """
    static_defaults = {
        "fingerprint": "35:9d:d0:c3:4a:80:d3:d8:86:f1:ca:f7:df:c4:f9:d8",
        "private_key": """-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQC9mC3WZN9UGLxgPBpP7H5jZMc6pKwOoSgre8yun6REFktn/Kz7\n
            DUt9jaR1UJyRzHxITfCfAIgSxPdGqB/oF1suMyWgu5i0625vavLB5z5kC8Hq3qZJ\n9zJO1poE1kyD+htiTtPWJ88e12xuH2XB/CZN9OpEiF98hAagiOE
            0EnOS5QIDAQAB\nAoGAE5XO1mDhORy9COvsg+kYPUhB1GsCYxh+v88wG7HeFDKBY6KUc/Kxo6yoGn5T\nTjRjekyi2KoDZHz4VlIzyZPwFS4I1bf3oCun
            VoAKzgLdmnTtvRNMC5jFOGc2vUgP\n9bSyRj3S1R4ClVk2g0IDeagko/jc8zzLEYuIK+fbkds79YECQQDt3vcevgegnkga\ntF4NsDmmBPRkcSHCqrANP
            /7vFcBQN3czxeYYWX3DK07alu6GhH1Y4sHbdm616uU0\nll7xbDzxAkEAzAtN2IyftNygV2EGiaGgqLyo/tD9+Vui2qCQplqe4jvWh/5Sparl\nOjmKo+
            uAW+hLrLVMnHzRWxbWU8hirH5FNQJATO+ZxCK4etXXAnQmG41NCAqANWB2\nB+2HJbH2NcQ2QHvAHUm741JGn/KI/aBlo7KEjFRDWUVUB5ji64BbUwCsM
            QJBAIku\nLGcjnBf/oLk+XSPZC2eGd2Ph5G5qYmH0Q2vkTx+wtTn3DV+eNsDfgMtWAJVJ5t61\ngU1QSXyhLPVlKpnnxuUCQC+xvvWjWtsLaFtAsZywJi
            qLxQzHts8XLGZptYJ5tLWV\nrtmYtBcJCN48RrgQHry/xWYeA4K/AFQpXfNPgprQ96Q=\n-----END RSA PRIVATE KEY-----\n"""
    }

    def key_json(self):
        template = self.static_defaults.copy()
        template.update({
            "name": self.name,
            "public_key": self.public_key,
            "user_id": self.user_id
        })
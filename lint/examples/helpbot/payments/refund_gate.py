REFUND_CAP = 100

def authorize(amount, approval_token=None):
    if amount > REFUND_CAP and not verify_signed_approval(approval_token):
        raise PermissionError("refund over cap needs a signed human approval")
    return True

def verify_signed_approval(token):
    return token is not None and token.startswith("signed:")

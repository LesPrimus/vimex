# VIMEX

**A simple wrapper around Httpx for interact with the Vimeo api.**

The first step to make a request to the vimeo api is to authenticate the request.

## Client Credentials authentication.

* Sync version.

```python
import vimex

auth = vimex.VimeoOAuth2ClientCredentials(
    client_id="my_client_id",
    client_secret="my_client_secret"
)

with vimex.VimeoClient(auth=auth) as client:
    res = client.get("https://api.vimeo.com")
```

## Authorization code authentication.

* Sync version.

```python
import vimex

auth = vimex.VimeoOauth2AuthorizationCode(
    client_id="my_client_id",
    client_secret="my_client_secret",
    state="some_state"
)

with vimex.VimeoClient(auth=auth) as client:
    res = client.get("https://api.vimeo.com/me")

```

### todo:

- Add a cache for the tokens.

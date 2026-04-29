# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

"""Transport connection testing utilities."""


def test_http_reachability(url: str, api_key: str | None) -> None:
    """Test HTTP reachability. Raises Exception on failure."""
    from urllib import request as urllib_request

    clean_url = url.strip().rstrip("/")
    if not clean_url.startswith("http"):
        clean_url = f"http://{clean_url}"

    req = urllib_request.Request(f"{clean_url}/health")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    with urllib_request.urlopen(req, timeout=5) as response:
        if response.status not in (200, 204):
            raise Exception(f"Unexpected status code {response.status}")


def test_s3_reachability(
    bucket: str,
    endpoint: str | None,
    access_key: str | None,
    secret_key: str | None,
    region: str | None,
) -> None:
    """Test S3 reachability. Raises Exception on failure."""
    try:
        import boto3  # pyright: ignore[reportMissingImports]
    except ImportError:
        raise RuntimeError("boto3 is not installed. S3 transport requires it.") from None

    client = boto3.client(
        "s3",
        endpoint_url=endpoint.strip() if endpoint else None,
        aws_access_key_id=access_key or None,
        aws_secret_access_key=secret_key or None,
        region_name=region or None,
    )
    client.head_bucket(Bucket=bucket)

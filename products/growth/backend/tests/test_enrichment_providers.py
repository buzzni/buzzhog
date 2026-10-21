import pytest

from products.growth.backend.enrichment.providers import EnrichmentProvider, HarmonicEnrichmentProvider, ProviderLookup


class _NoOpProvider(EnrichmentProvider):
    name = "noop"

    async def enrich_by_domain(self, domain: str) -> ProviderLookup:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_enrichment_statuses_for_defaults_to_an_empty_dict_for_a_provider_without_tracking():
    assert await _NoOpProvider().enrichment_statuses_for(["urn:harmonic:enrichment:abc"]) == {}


@pytest.mark.asyncio
async def test_harmonic_provider_fails_loudly_without_a_client():
    with pytest.raises(NotImplementedError):
        await HarmonicEnrichmentProvider().enrich_by_domain("posthog.com")

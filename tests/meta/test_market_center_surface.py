from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_market_surface_promotes_public_search_and_dedicated_detail_route():
    html = (REPO_ROOT / "sharelife" / "webui" / "market.html").read_text(encoding="utf-8")

    assert 'id="marketTopBar"' in html
    assert 'id="marketGlobalSearch"' in html
    assert html.index('id="marketGlobalSearch"') < html.index('id="marketSortBy"')
    assert 'id="marketControlRow"' in html
    assert 'id="marketFilterSidebar"' in html
    assert 'id="marketSidebarCategoryList"' in html
    assert 'id="marketCatalogGrid"' in html
    assert 'id="btnMarketListCatalog" class="btn-ghost"' in html
    assert 'id="marketCompareStrip"' not in html
    assert 'id="btnMarketRefreshInstallations"' not in html
    assert "market.operations.heading" not in html
    assert "hero.badge.signed_verified" not in html
    assert 'id="marketCatalogMetrics"' not in html
    assert 'id="marketFeaturedSpotlight"' not in html
    assert 'id="marketTrendingRack"' not in html
    assert 'id="marketDetailArea"' not in html
    assert 'id="marketDetailVariantTabs"' not in html
    assert 'id="marketDetailMemberActions"' not in html
    assert 'id="marketDetailPublicFacts"' not in html
    assert 'id="marketDetailActionRail"' not in html
    assert 'id="marketInstallSectionList"' not in html
    assert 'id="marketInstallSectionSummary"' not in html
    assert 'id="marketUploadDropzone"' not in html
    assert 'id="marketUploadFileName"' not in html
    assert 'id="btnMarketCatalogCompare"' not in html
    assert 'id="marketCompareShell"' not in html


def test_market_detail_surface_hosts_member_actions_without_variant_tabs_or_upload_shell():
    html = (REPO_ROOT / "sharelife" / "webui" / "market_detail.html").read_text(encoding="utf-8")

    assert 'id="marketDetailArea"' in html
    assert 'id="marketDetailVariantTabs"' not in html
    assert 'id="marketDetailMemberActions"' not in html
    assert 'id="marketDetailPublicFacts"' not in html
    assert 'id="marketDetailActionRail"' not in html
    assert 'id="marketDetailControlStore"' in html
    assert 'id="marketMemberConsoleLink" href="/member" class="market-link hidden"' in html
    assert 'id="marketReviewerConsoleLink" href="/reviewer" class="market-link hidden"' in html
    assert 'id="marketAdminConsoleLink" href="/admin" class="market-link hidden"' in html
    assert 'id="marketFullConsoleLink" href="/" class="market-link hidden"' in html
    assert 'id="marketDetailActionCluster"' not in html
    assert 'id="marketDetailInstallOptionsShell"' in html
    assert 'id="marketInstallSectionList"' in html
    assert 'id="marketInstallSectionSummary"' in html
    assert 'id="btnMarketDetailTrial"' not in html
    assert 'id="btnMarketDetailInstall"' not in html
    assert 'id="btnMarketDetailRefreshInstallations"' not in html
    assert 'id="btnMarketDetailSubmitTemplate"' not in html
    assert 'id="btnMarketDetailSubmitProfilePack"' not in html
    assert 'id="marketUploadDropzone"' not in html
    assert 'id="marketUploadFileName"' not in html
    assert 'id="marketSubmitPackageFile"' not in html
    assert 'id="btnMarketCatalogCompare"' not in html
    assert 'id="btnMarketCatalogDownload"' not in html
    assert 'id="marketSummary"' not in html
    assert 'id="marketCompareShell"' in html

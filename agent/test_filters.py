from filters import JobCard, qualify


def test_experian_architect_passes():
    r = qualify(
        JobCard(
            title="Solution Architect (Microsoft .NET/Azure Cloud)",
            company="Experian",
            location="Hyderabad",
            experience="7-12 Yrs",
            salary="Not Disclosed",
            skills="Azure, Architecture",
        )
    )
    assert r.ok, r.reasons


def test_search_query_not_proof_of_dotnet():
    r = qualify(
        JobCard(
            title="Solution Architect (Python)",
            company="Nexturn",
            location="Hyderabad",
            experience="10-19 Yrs",
            skills="Python, AWS",
        )
    )
    assert not r.ok
    assert "no .NET in title/skills" in r.reasons


def test_aspnet_not_skipped_as_sap():
    r = qualify(
        JobCard(
            title="ASP.Net Lead",
            location="Hyderabad",
            experience="8-12 Yrs",
            skills="ASP.Net Core, Web API",
        )
    )
    assert r.ok, r.reasons


def test_ctc_under_50_skipped():
    r = qualify(
        JobCard(
            title=".NET Lead",
            location="Hyderabad",
            experience="10-15 Yrs",
            salary="15-25 Lacs PA",
            skills=".NET",
        )
    )
    assert not r.ok
    assert any("CTC" in x for x in r.reasons)


def test_other_metro_without_hyd_skipped():
    r = qualify(
        JobCard(
            title=".NET Architect",
            location="Bengaluru",
            experience="10-15 Yrs",
            skills=".NET",
        )
    )
    assert not r.ok
    assert "other metro only" in r.reasons


if __name__ == "__main__":
    test_experian_architect_passes()
    test_search_query_not_proof_of_dotnet()
    test_aspnet_not_skipped_as_sap()
    test_ctc_under_50_skipped()
    test_other_metro_without_hyd_skipped()
    print("ok")

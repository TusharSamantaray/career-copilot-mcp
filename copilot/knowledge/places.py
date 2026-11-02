"""Job hubs by field, for "should I move?" conversations.

Durable, general facts only. Cost tier: 1 lower, 2 middle, 3 high cost of
living. Always tell the user to verify current demand, pay and visa rules.
"""

HUBS = [
    # city, country, families strongest there, cost tier, note
    ("San Francisco Bay Area", "US", ["engineering", "product", "data",
     "design", "management"], 3, "Deepest tech and AI market; highest "
     "pay and highest costs."),
    ("Seattle", "US", ["engineering", "product", "data", "management"], 3,
     "Big cloud and e-commerce employers; no state income tax."),
    ("New York", "US", ["finance", "business", "product", "design",
     "data"], 3, "Finance, media, marketing and a large startup scene."),
    ("Austin", "US", ["engineering", "business", "product"], 2,
     "Growing tech hub with lower costs than the coasts."),
    ("Boston", "US", ["engineering", "data", "people"], 3,
     "Healthcare, biotech, universities and robotics."),
    ("Chicago", "US", ["finance", "operations", "business"], 2,
     "Trading, consulting, logistics; mid-range costs."),
    ("Atlanta", "US", ["operations", "business", "finance"], 2,
     "Logistics, fintech and corporate headquarters."),
    ("Raleigh-Durham", "US", ["engineering", "data"], 2,
     "Research Triangle: tech, pharma and universities."),
    ("Dallas", "US", ["finance", "operations", "business"], 2,
     "Corporate headquarters, finance and sales roles."),
    ("Toronto", "CA", ["finance", "engineering", "design", "business"],
     2, "Canada's largest market: banks, tech and media."),
    ("Vancouver", "CA", ["engineering", "design"], 3,
     "Tech, games and film; high housing costs."),
    ("Montreal", "CA", ["engineering", "data", "design"], 2,
     "AI research, games; French helps a lot."),
    ("London", "GB", ["finance", "product", "business", "engineering",
     "design"], 3, "Europe's biggest finance and tech market."),
    ("Dublin", "IE", ["business", "engineering", "operations"], 3,
     "European headquarters of many tech firms; sales and support "
     "roles are plentiful."),
    ("Berlin", "DE", ["engineering", "design", "product"], 2,
     "Startup capital of Europe; English widely used in tech."),
    ("Amsterdam", "NL", ["engineering", "product", "business"], 3,
     "International companies; English-friendly workplaces."),
    ("Munich", "DE", ["engineering", "operations"], 3,
     "Automotive, industrial and enterprise tech."),
    ("Lisbon", "PT", ["engineering", "business", "design"], 2,
     "Growing startup and remote-work hub with lower costs."),
    ("Bengaluru", "IN", ["engineering", "product", "data", "design"], 2,
     "India's largest tech and startup ecosystem."),
    ("Hyderabad", "IN", ["engineering", "data", "operations"], 1,
     "Large global capability centres of big tech; lower costs."),
    ("Pune", "IN", ["engineering", "operations"], 1,
     "IT services, automotive and manufacturing."),
    ("Delhi NCR", "IN", ["business", "finance", "operations"], 2,
     "Sales, consulting, fintech and corporate roles."),
    ("Mumbai", "IN", ["finance", "business", "design"], 2,
     "Finance, media and marketing capital."),
    ("Chennai", "IN", ["engineering", "operations"], 1,
     "SaaS companies, manufacturing and operations."),
    ("Singapore", "SG", ["finance", "business", "engineering"], 3,
     "Regional headquarters for Asia-Pacific; finance and sales."),
    ("Sydney", "AU", ["finance", "engineering", "business"], 3,
     "Australia's finance and tech centre."),
    ("Dubai", "AE", ["business", "finance", "operations"], 3,
     "Sales, finance and hospitality; no personal income tax."),
]

COUNTRY_ALIASES = {
    "usa": "US", "united states": "US", "america": "US", "us": "US",
    "canada": "CA", "uk": "GB", "united kingdom": "GB", "england": "GB",
    "britain": "GB", "ireland": "IE", "germany": "DE",
    "netherlands": "NL", "portugal": "PT", "india": "IN",
    "singapore": "SG", "australia": "AU", "uae": "AE",
    "united arab emirates": "AE",
}

CAUTIONS = [
    "Check real openings in your field there before committing: search "
    "the city on a job board and count roles at your level.",
    "Compare pay against cost of living, not pay alone.",
    "Moving countries needs a work visa or permit; confirm the route "
    "before you resign or relocate.",
    "Try remote or a short visit first if you can.",
]

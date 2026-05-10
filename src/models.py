from pydantic import BaseModel, Field
from typing import List, Optional

class VendorInput(BaseModel):
    website: Optional[str] = None
    instagram_page: Optional[str] = None
    category: str
    location: str
    product_details: str

class SalesOutput(BaseModel):
    business_summary: str
    pain_point_analysis: str
    qualification_score: int = Field(..., ge=1, le=10, description="Qualification score from 1 to 10")
    outreach_strategy: str
    personalized_sales_pitch: str
    follow_up_suggestions: List[str]

class MarketingOutput(BaseModel):
    ad_campaign_ideas: List[str]
    instagram_content_ideas: List[str]
    launch_campaign_concepts: List[str]
    reels_post_hooks: List[str]
    growth_suggestions: List[str]

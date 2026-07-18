#!/usr/bin/env python3
"""Browser review for the read-only Governance Workspace."""
from __future__ import annotations
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL=os.environ.get("CAMPAIGNOS_URL","http://127.0.0.1:4173")
ARTIFACT_DIR=Path(os.environ.get("CAMPAIGNOS_ARTIFACT_DIR","artifacts/governance-runtime"))

def require(condition:bool,message:str)->None:
    if not condition: raise AssertionError(message)

def review(browser,viewport:dict,reduced_motion:str,label:str)->None:
    context=browser.new_context(viewport=viewport,reduced_motion=reduced_motion)
    page=context.new_page(); errors=[]
    page.on("console",lambda message: errors.append(message.text) if message.type=="error" else None)
    page.on("pageerror",lambda error: errors.append(str(error)))
    page.goto(BASE_URL,wait_until="networkidle")
    tab=page.locator('[data-module="governance"]'); tab.wait_for(state="visible"); tab.click()
    page.locator('[data-view="governance"]').wait_for(state="visible")
    page.locator("#governanceBrandStatus").wait_for(state="visible")
    require(page.locator("#governanceBrandStatus").inner_text()=="SETUP REQUIRED","brand status must remain setup-required")
    require(page.locator("#governanceApprovalCount").inner_text()=="1","pending approval count mismatch")
    require(page.locator("#governanceAssignmentCount").inner_text()=="1","assignment count mismatch")
    require(page.locator("#governanceModule button").count()==0,"governance workspace must expose no action buttons")
    require("Coordinate 04" in page.locator("#activeModuleStatus").inner_text(),"module status label mismatch")
    require(page.evaluate("document.activeElement?.id")=="governance-title","module title must receive focus")
    dimensions=page.evaluate("() => ({clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth})")
    require(dimensions["scrollWidth"]<=dimensions["clientWidth"]+1,f"horizontal overflow: {dimensions}")
    require(not errors,f"runtime errors: {errors}")
    ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=ARTIFACT_DIR/f"{label}-governance.png",full_page=True)
    context.close()

def main()->int:
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        review(browser,{"width":1440,"height":1000},"no-preference","desktop")
        review(browser,{"width":390,"height":844},"no-preference","mobile")
        review(browser,{"width":1280,"height":800},"reduce","reduced-motion")
        browser.close()
    print("[OK] Governance Workspace desktop, mobile, focus and reduced-motion review")
    return 0
if __name__=="__main__": raise SystemExit(main())

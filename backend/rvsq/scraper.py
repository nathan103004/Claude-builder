# rvsq/scraper.py — stub, will be fully implemented in Task 6
from __future__ import annotations
from selenium import webdriver
from models.rvsq_models import ClinicCard, RVSQError


def parse_clinic_cards(driver: webdriver.Chrome) -> list[ClinicCard] | RVSQError:
    return []


def parse_clinic_cards_from_html(html: str) -> list[ClinicCard] | RVSQError:
    return []

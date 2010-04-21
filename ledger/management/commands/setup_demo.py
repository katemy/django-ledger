#!/usr/bin/python

from django.core.management.base import BaseCommand

from ledger.demo import setup_demo


class Command(BaseCommand):
    help = "Setup minibooks demo"
    requires_model_validation = False

    def handle(self, **options):
        setup_demo()

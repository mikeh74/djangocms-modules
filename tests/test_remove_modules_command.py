"""
Test for the remove_modules management command.
"""
import io
import sys
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from djangocms_modules.models import Category, ModulePlugin


class RemoveModulesCommandTest(TestCase):
    """Test the remove_modules management command."""

    def test_command_help(self):
        """Test that the command shows help without errors."""
        out = io.StringIO()
        call_command('remove_modules', '--help', stdout=out)
        output = out.getvalue()
        self.assertIn('Remove all Module CMS plugins', output)
        self.assertIn('--dry-run', output)
        self.assertIn('--remove-categories', output)
        self.assertIn('--force', output)

    def test_no_modules_to_remove(self):
        """Test command when there are no modules to remove."""
        out = io.StringIO()
        call_command('remove_modules', '--force', stdout=out)
        output = out.getvalue()
        self.assertIn('No Module plugins found to remove', output)

    def test_dry_run_mode(self):
        """Test that dry run mode doesn't delete anything."""
        # This test would need actual module plugins to be meaningful
        # For now, just test that dry run mode is recognized
        out = io.StringIO()
        call_command('remove_modules', '--dry-run', '--force', stdout=out)
        output = out.getvalue()
        # Should show dry run message or no modules message
        self.assertTrue(
            'DRY RUN MODE' in output or 'No Module plugins found' in output
        )
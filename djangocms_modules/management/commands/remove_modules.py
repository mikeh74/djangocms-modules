from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cms.models import CMSPlugin
from djangocms_modules.models import Category, ModulePlugin


def pluralize(value, arg='s'):
    """
    Local replacement for Django's removed pluralize function.
    Returns the plural suffix for a given value.

    Args:
        value: The count/value to check for pluralization
        arg: Either 's' (default) or 'singular,plural' format

    Returns:
        Empty string if value is 1, otherwise the appropriate suffix
    """
    if value == 1:
        return ''

    if ',' in arg:
        singular, plural = arg.split(',', 1)
        return plural

    return arg


class Command(BaseCommand):
    help = 'Remove all Module CMS plugins and optionally their categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting it',
        )
        parser.add_argument(
            '--remove-categories',
            action='store_true',
            help='Also remove empty categories after removing modules',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts',
        )
        parser.add_argument(
            '--verbosity',
            type=int,
            choices=[0, 1, 2],
            default=1,
            help='Verbosity level; 0=minimal output, 1=normal output, 2=verbose output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        remove_categories = options['remove_categories']
        force = options['force']
        verbosity = options['verbosity']

        try:
            # Count what we'll be working with
            module_plugins = ModulePlugin.objects.all()
            module_count = module_plugins.count()
            categories = Category.objects.all()
            category_count = categories.count()

            if module_count == 0:
                if verbosity >= 1:
                    self.stdout.write(
                        self.style.WARNING('No Module plugins found to remove.')
                    )
                return

            # Get all child plugins that will be affected
            all_child_plugins = []
            for module_plugin in module_plugins:
                # Get all descendants (child plugins) of this module
                # Using get_tree to get all descendants, excluding the root plugin itself
                tree = module_plugin.get_tree()
                descendants = tree.exclude(pk=module_plugin.pk)
                all_child_plugins.extend(descendants)

            child_plugin_count = len(all_child_plugins)
            total_plugins = module_count + child_plugin_count

            # Display summary
            if verbosity >= 1:
                self.stdout.write(
                    self.style.WARNING(f'Found {module_count} Module plugin{pluralize(module_count)} '
                                       f'with {child_plugin_count} child plugin{pluralize(child_plugin_count)}')
                )
                if remove_categories:
                    self.stdout.write(
                        self.style.WARNING(f'Found {category_count} categor{pluralize(category_count, "y,ies")} '
                                           f'that will be removed')
                    )

            if dry_run:
                if verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS('DRY RUN MODE - No changes will be made')
                    )
            elif not force:
                # Ask for confirmation
                confirm_msg = (
                    f'This will permanently delete {total_plugins} plugin{pluralize(total_plugins)} '
                    f'({module_count} Module plugins and {child_plugin_count} child plugins)'
                )
                if remove_categories:
                    confirm_msg += f' and {category_count} categor{pluralize(category_count, "y,ies")}'
                confirm_msg += '.\n\nAre you sure? Type "yes" to continue: '

                confirmation = input(confirm_msg)
                if confirmation.lower() != 'yes':
                    if verbosity >= 1:
                        self.stdout.write(
                            self.style.ERROR('Operation cancelled.')
                        )
                    return

            if verbosity >= 2:
                self.stdout.write('Detailed breakdown:')
                for module_plugin in module_plugins:
                    tree = module_plugin.get_tree()
                    descendants = tree.exclude(pk=module_plugin.pk)
                    self.stdout.write(
                        f'  Module "{module_plugin.module_name}" (ID: {module_plugin.pk}) '
                        f'has {len(descendants)} child plugin{pluralize(len(descendants))}'
                    )

            if not dry_run:
                # Perform the actual deletion
                try:
                    with transaction.atomic():
                        deleted_counts = self._delete_plugins(
                            module_plugins, remove_categories, verbosity
                        )

                        if verbosity >= 1:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Successfully deleted {deleted_counts["modules"]} Module plugins, '
                                    f'{deleted_counts["children"]} child plugins'
                                )
                            )
                            if remove_categories and deleted_counts["categories"] > 0:
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Successfully deleted {deleted_counts["categories"]} '
                                        f'empty categor{pluralize(deleted_counts["categories"], "y,ies")}'
                                    )
                                )
                except Exception as e:
                    raise CommandError(f'Error during deletion: {e}')
            else:
                if verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS('Dry run completed. Use --force to skip confirmation.')
                    )

        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')

    def _delete_plugins(self, module_plugins, remove_categories, verbosity):
        """Delete the plugins and optionally categories."""
        deleted_counts = {
            'modules': 0,
            'children': 0,
            'categories': 0,
        }

        # Delete each module plugin (which will cascade to children)
        for module_plugin in module_plugins:
            # Count children before deletion
            tree = module_plugin.get_tree()
            descendants = tree.exclude(pk=module_plugin.pk)
            child_count = len(descendants)

            if verbosity >= 2:
                self.stdout.write(
                    f'Deleting Module "{module_plugin.module_name}" '
                    f'and {child_count} child plugin{pluralize(child_count)}...'
                )

            # Delete the module plugin (this will cascade to children due to CMSPlugin tree structure)
            module_plugin.delete()

            deleted_counts['modules'] += 1
            deleted_counts['children'] += child_count

        # Optionally remove empty categories
        if remove_categories:
            # Find categories that no longer have any plugins
            empty_categories = []
            for category in Category.objects.all():
                # Check if this category has any plugins left
                # Use the same method as the existing code in models.py
                plugins_count = (
                    category.modules
                    .get_plugins()
                    .count()
                )
                if plugins_count == 0:
                    empty_categories.append(category)

            for category in empty_categories:
                if verbosity >= 2:
                    self.stdout.write(f'Deleting empty category "{category.name}"...')
                category.delete()
                deleted_counts['categories'] += 1

        return deleted_counts

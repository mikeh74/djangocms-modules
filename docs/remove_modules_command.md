# Remove Modules Management Command

The `remove_modules` management command allows you to safely delete all Module CMS plugins from your Django CMS installation. This is useful when you want to remove the djangocms-modules package but want to keep your migration history intact.

## Usage

```bash
python manage.py remove_modules [options]
```

## Options

- `--dry-run`: Show what would be deleted without actually deleting anything
- `--remove-categories`: Also remove empty categories after removing modules
- `--force`: Skip confirmation prompts (useful for automated scripts)
- `--verbosity {0,1,2}`: Control output level (0=minimal, 1=normal, 2=verbose)

## Examples

### Preview what would be deleted (recommended first step)
```bash
python manage.py remove_modules --dry-run --verbosity=2
```

### Remove all modules with confirmation
```bash
python manage.py remove_modules
```

### Remove all modules and empty categories without confirmation
```bash
python manage.py remove_modules --remove-categories --force
```

### Remove modules with minimal output
```bash
python manage.py remove_modules --force --verbosity=0
```

## What gets deleted

1. **Module plugins**: All instances of ModulePlugin
2. **Child plugins**: All plugins that are children of Module plugins
3. **Categories** (if `--remove-categories` is used): Empty Category instances

## Safety features

- **Confirmation prompt**: By default, asks for confirmation before deletion
- **Dry run mode**: Preview deletions without making changes
- **Transaction safety**: All deletions happen in a database transaction
- **Detailed feedback**: Shows counts of what will be/was deleted
- **Verbose mode**: Optional detailed breakdown of each module and its children

## Important notes

- This command cannot be undone once executed (unless you have database backups)
- Module plugins are deleted using Django's model deletion, which properly handles cascading
- Child plugins are automatically deleted when their parent Module plugin is deleted
- The command preserves migration history, allowing future re-installation of the package
- Empty categories are only deleted if explicitly requested with `--remove-categories`

## Before removing the package

1. Run with `--dry-run` first to see what will be affected
2. Make a database backup
3. Run the command: `python manage.py remove_modules`
4. Verify the modules are removed from your CMS pages
5. Remove the package from your requirements and INSTALLED_APPS
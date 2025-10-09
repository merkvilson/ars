"""
cmd> pipreqs --print
"""
import os
import ast
import sys
from stdlib_list import stdlib_list
import importlib.metadata
import pkg_resources

def find_imports_in_file(file_path):
    """Parse imports from a single .py file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception:
        return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # Only absolute imports
                imports.add(node.module.split(".")[0])
    
    return imports

def get_local_modules(project_path):
    """Identify local modules in the project."""
    local_modules = set()
    
    for item in os.listdir(project_path):
        item_path = os.path.join(project_path, item)
        
        # Single .py file (excluding special files)
        if item.endswith('.py') and not item.startswith('__'):
            local_modules.add(item[:-3])
        
        # Directory with __init__.py is a package
        elif os.path.isdir(item_path):
            if os.path.exists(os.path.join(item_path, '__init__.py')):
                local_modules.add(item)
    
    return local_modules

def build_import_to_package_map():
    """Build a mapping from import names to PyPI package names dynamically."""
    import_to_package = {}
    
    # Get all installed distributions
    for dist in pkg_resources.working_set:
        package_name = dist.project_name
        
        # Try to get top-level modules provided by this package
        try:
            if dist.has_metadata('top_level.txt'):
                top_level = dist.get_metadata('top_level.txt').strip().split('\n')
                for module in top_level:
                    module = module.strip()
                    if module:
                        import_to_package[module] = package_name
        except Exception:
            pass
        
        # Fallback: assume package name matches import name
        if package_name.lower().replace('-', '_') not in import_to_package:
            import_to_package[package_name.lower().replace('-', '_')] = package_name
    
    return import_to_package

def find_third_party_modules(project_path=".", exclude_local=True):
    """Return third-party modules used in the project with versions."""
    stdlib = set(stdlib_list())
    all_imports = set()
    
    # Get local modules
    local_modules = get_local_modules(project_path) if exclude_local else set()
    
    # Find all imports in the project
    for root, _, files in os.walk(project_path):
        # Skip common non-source directories
        if any(skip in root for skip in ['.venv', 'venv', '__pycache__', '.git', 
                                          'node_modules', '.tox', 'build', 'dist', 
                                          '.pytest_cache', '__pypackages__']):
            continue
            
        for file in files:
            if file.endswith(".py"):
                all_imports |= find_imports_in_file(os.path.join(root, file))
    
    # Build import to package mapping
    import_to_package = build_import_to_package_map()
    
    # Filter to third-party only
    third_party = {}
    
    for module in sorted(all_imports):
        # Skip standard library, private modules, and local modules
        if module in stdlib or module.startswith("_") or module in local_modules:
            continue
        
        # Find the actual package name
        package_name = import_to_package.get(module, module)
        
        # Avoid duplicates (if multiple imports map to same package)
        if package_name in third_party:
            continue
        
        # Try to get version information
        try:
            version = importlib.metadata.version(package_name)
            third_party[package_name] = version
        except importlib.metadata.PackageNotFoundError:
            # Not installed or truly local
            pass
    
    return third_party

def generate_requirements(project_path=".", output_file="requirements.txt", show_version=False):
    """Generate a requirements.txt file."""
    modules = find_third_party_modules(project_path)
    
    print(f"Found {len(modules)} third-party packages:\n")
    
    requirements = []
    
    for module, version in sorted(modules.items()):
        if show_version:
            requirements.append(f"{module}=={version}")
            print(f"✓ {module}=={version}")
        else:
            requirements.append(module)
            print(f"✓ {module}")
    
    # Write requirements.txt
    if requirements:
        with open(output_file, "w") as f:
            f.write("\n".join(requirements) + "\n")
        version_note = "with versions" if show_version else "without versions"
        print(f"\n✅ Generated {output_file} with {len(requirements)} packages ({version_note})")
    else:
        print("\n⚠️  No third-party packages found")
    
    return requirements

if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else ".."
    show_version = "--no-version" not in sys.argv
    generate_requirements(project_path, show_version=False)
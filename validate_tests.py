"""Validate test file syntax and structure."""

import ast
import sys
from pathlib import Path


def validate_test_file(filepath):
    """Validate a test file has correct Python syntax and structure."""
    print(f"\nValidating {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file to check syntax
        tree = ast.parse(content, filename=str(filepath))
        
        # Count test functions
        test_functions = []
        fixtures = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_functions.append(node.name)
                # Check for @pytest.fixture decorator
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Attribute):
                        if dec.attr == 'fixture':
                            fixtures.append(node.name)
                    elif isinstance(dec, ast.Name) and dec.id == 'fixture':
                        fixtures.append(node.name)
        
        print(f"  ✓ Syntax valid")
        print(f"  ✓ Found {len(fixtures)} fixtures")
        print(f"  ✓ Found {len(test_functions)} test functions")
        
        if test_functions:
            print(f"  Tests: {', '.join(test_functions[:3])}{'...' if len(test_functions) > 3 else ''}")
        
        return True
        
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Validate all test files."""
    test_dir = Path('tests/unit')
    test_files = list(test_dir.glob('test_*.py'))
    
    print(f"Found {len(test_files)} test files to validate")
    
    results = []
    for test_file in test_files:
        results.append(validate_test_file(test_file))
    
    print("\n" + "="*60)
    if all(results):
        print(f"✓ All {len(results)} test files are valid!")
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"✗ {failed} test file(s) failed validation")
        return 1


if __name__ == '__main__':
    sys.exit(main())

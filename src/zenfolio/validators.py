"""
This module contains validation functions for the ZenFolio website generator.
"""
from pathlib import Path

from .zenfolio import get_output_dir


def validate_site(content_dir: Path):
    """Validate configuration and content files"""
    print(f"🔍 Validating academic website in {content_dir}")
    
    errors = []
    warnings = []
    
    if not content_dir.exists():
        errors.append(f"Content directory '{content_dir}' does not exist")
        print("❌ Validation failed:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    required_files = ["config.py", "index.md", "publications.bib"]
    for filename in required_files:
        file_path = content_dir / filename
        if not file_path.exists():
            errors.append(f"Required file '{filename}' is missing")
    
    try:
        from zencfg import load_config_from_file
        config = load_config_from_file(content_dir / "config.py", "config")
        print("✅ Configuration loaded and validated successfully")
        
        if not config.author.name or config.author.name == "Your Name":
            warnings.append("Author name is not customized")
        
        if not config.author.email or config.author.email == "your.email@example.com":
            warnings.append("Author email is not customized")
        
        if not config.site.base_url or config.site.base_url == "https://yourdomain.com":
            warnings.append("Site URL is not customized")
            
        content_files = ["news.py", "projects.py", "talks.py"]
        for filename in content_files:
            file_path = content_dir / filename
            if file_path.exists():
                print(f"✅ Found {filename}")
            else:
                warnings.append(f"Optional content file '{filename}' is missing")
    
    except ImportError:
        errors.append("Cannot import zencfg - please install with 'pip install zencfg'")
    except FileNotFoundError:
        errors.append("config.py file not found")
    except (TypeError, ValueError, AttributeError) as e:
        errors.append(f"Configuration validation failed: {e}")
        errors.append("Check your config.py file for type mismatches or missing required fields")
    except Exception as e:
        errors.append(f"Unexpected error loading configuration: {e}")
    
    static_dir = content_dir / "static"
    if not static_dir.exists():
        warnings.append("Static directory is missing")
    else:
        profile_img = static_dir / "profile.jpg"
        if not profile_img.exists():
            warnings.append("Profile image (static/profile.jpg) is missing")
    
    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    if warnings:
        print("⚠️  Validation passed with warnings:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not warnings:
        print("✅ All validation checks passed!")
    
    return len(errors) == 0


def validate_generated_site(content_dir: Path, debug: bool = False) -> bool:
    """Validate the generated site for common deployment issues"""
    output_dir = content_dir / get_output_dir(content_dir)
    
    if not output_dir.exists():
        print("❌ Output directory doesn't exist - run build first")
        return False
    
    issues_found = []
    warnings_found = []
    
    html_files = list(output_dir.glob("**/*.html"))
    if html_files:
        print(f"🔍 Validating {len(html_files)} HTML files...")
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                
                if '{static}' in content:
                    issues_found.append(f"Unprocessed {{static}} placeholder in {html_file.relative_to(output_dir)}")
                
                import re
                malformed_urls = re.findall(r'href="(?!https?://)[^"]*//[^"]*"', content)
                if malformed_urls:
                    for url in malformed_urls[:2]:
                        warnings_found.append(f"Malformed internal URL {url} in {html_file.relative_to(output_dir)}")
                
            except Exception as e:
                if debug:
                    warnings_found.append(f"Could not read {html_file.relative_to(output_dir)}: {e}")
    
    critical_files = ['.nojekyll']
    for file_name in critical_files:
        if not (output_dir / file_name).exists():
            issues_found.append(f"Missing critical file: {file_name}")
    
    static_dir = output_dir / 'static'
    if static_dir.exists() and not any(static_dir.iterdir()):
        warnings_found.append("Static directory is empty - images/assets may not be copied")
    
    if issues_found:
        print("❌ CRITICAL ISSUES FOUND:")
        for issue in issues_found:
            print(f"   • {issue}")
        print("🚨 These issues will cause broken functionality on the deployed site!")
        return False
    
    if warnings_found:
        print("⚠️  Warnings found:")
        for warning in warnings_found[:5]:
            print(f"   • {warning}")
        if len(warnings_found) > 5:
            print(f"   ... and {len(warnings_found) - 5} more warnings")
    
    if not issues_found and not warnings_found:
        print("✅ Site validation passed - no issues found!")
    elif not issues_found:
        print("✅ Site validation passed with warnings")
    
    return True

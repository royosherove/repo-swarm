#!/usr/bin/env python3
"""
Simple unit tests to verify the workflow behavior.
These tests focus on BEHAVIOR, not implementation details.
"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_workflow_has_save_to_dynamo_method():
    """
    Test that the workflow has the _save_to_dynamo method with the expected signature.
    This tests the BEHAVIOR: the method exists and can be called.
    """
    from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
    import inspect
    
    workflow = InvestigateSingleRepoWorkflow()
    
    # Verify the method exists
    assert hasattr(workflow, '_save_to_dynamo'), "Workflow should have _save_to_dynamo method"
    
    # Verify it's callable
    assert callable(workflow._save_to_dynamo), "_save_to_dynamo should be callable"
    
    # Verify the signature
    sig = inspect.signature(workflow._save_to_dynamo)
    params = list(sig.parameters.keys())
    
    expected_params = [
        'investigation_result', 'repo_name', 'repo_url',
        'latest_commit', 'branch_name', 'all_results', 'arch_file_path',
        'prompt_versions'
    ]
    
    assert params == expected_params, f"Expected {expected_params}, got {params}"
    
    print("✅ Workflow has the correct _save_to_dynamo method signature")


def test_workflow_has_cache_check_method():
    """
    Test that the workflow has cache checking functionality.
    This tests BEHAVIOR: the workflow can check if investigation is needed.
    """
    from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
    import inspect
    
    workflow = InvestigateSingleRepoWorkflow()
    
    # Verify the cache check method exists
    assert hasattr(workflow, '_check_cache'), "Workflow should have _check_cache method"
    assert callable(workflow._check_cache), "_check_cache should be callable"
    
    # Verify the signature includes the necessary parameters
    sig = inspect.signature(workflow._check_cache)
    params = list(sig.parameters.keys())
    
    # Should have parameters for repo identification and prompt versions
    assert 'repo_name' in params, "Cache check should accept repo_name"
    assert 'repo_url' in params, "Cache check should accept repo_url"
    assert 'repo_path' in params, "Cache check should accept repo_path"
    assert 'prompt_versions' in params, "Cache check should accept prompt_versions"
    
    print("✅ Workflow has cache checking functionality")


def test_workflow_has_required_methods():
    """
    Test that the workflow has all the required methods for investigation.
    This tests BEHAVIOR: the workflow provides the expected interface.
    """
    from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
    
    workflow = InvestigateSingleRepoWorkflow()
    
    # Test that essential methods exist
    required_methods = [
        'run',  # Main workflow entry point
        '_check_cache',  # Cache checking
        '_save_to_dynamo',  # Metadata saving
        '_process_analysis_steps',  # Analysis processing
    ]
    
    for method_name in required_methods:
        assert hasattr(workflow, method_name), f"Workflow should have {method_name} method"
        assert callable(getattr(workflow, method_name)), f"{method_name} should be callable"
    
    print("✅ Workflow has all required methods")


def test_workflow_run_method_uses_pydantic_models():
    """
    Test that the workflow run method uses Pydantic models for input/output.
    This tests BEHAVIOR: the workflow has type-safe interfaces.
    """
    from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
    from models import InvestigateSingleRepoRequest, InvestigateSingleRepoResult
    import inspect
    
    workflow = InvestigateSingleRepoWorkflow()
    
    # Check the run method signature
    sig = inspect.signature(workflow.run)
    params = list(sig.parameters.values())
    
    # Should have one parameter for the request
    assert len(params) == 1, "Run method should have exactly one parameter"
    
    request_param = params[0]
    assert request_param.name == 'request', "Parameter should be named 'request'"
    assert request_param.annotation == InvestigateSingleRepoRequest, "Parameter should be InvestigateSingleRepoRequest"
    
    # Check return type annotation
    assert sig.return_annotation == InvestigateSingleRepoResult, "Return type should be InvestigateSingleRepoResult"
    
    print("✅ Workflow run method uses Pydantic models")


def test_pydantic_models_for_cache_activities():
    """
    Test that the cache activities use proper Pydantic models.
    This tests BEHAVIOR: activities have type-safe interfaces.
    """
    from models import CacheCheckInput, CacheCheckOutput, SaveMetadataInput, SaveMetadataOutput
    
    # Test CacheCheckInput can be created with required fields
    cache_input = CacheCheckInput(
        repo_name="test-repo",
        repo_url="https://github.com/test/repo",
        repo_path="/tmp/test-repo",
        prompt_versions={"test": "1"}
    )
    assert cache_input.repo_name == "test-repo"
    assert cache_input.prompt_versions == {"test": "1"}
    
    # Test SaveMetadataInput can be created with required fields
    save_input = SaveMetadataInput(
        repo_name="test-repo",
        repo_url="https://github.com/test/repo",
        latest_commit="abc123def456",
        branch_name="main",
        analysis_summary={"steps": 5},
        prompt_versions={"test": "1"}
    )
    assert save_input.repo_name == "test-repo"
    assert save_input.latest_commit == "abc123def456"
    
    print("✅ Cache activities use proper Pydantic models")


def test_workflow_request_model_validation():
    """
    Test that the workflow request model validates inputs properly.
    This tests BEHAVIOR: invalid inputs are caught early.
    """
    from models import InvestigateSingleRepoRequest, ConfigOverrides
    from pydantic import ValidationError
    import pytest
    
    # Test valid request creation
    valid_request = InvestigateSingleRepoRequest(
        repo_name="test-repo",
        repo_url="https://github.com/test/repo",
        repo_type="backend",
        force=True,
        config_overrides=ConfigOverrides(
            claude_model="claude-3-sonnet-20240229",
            max_tokens=4000
        )
    )
    assert valid_request.repo_name == "test-repo"
    assert valid_request.force == True
    assert valid_request.config_overrides.claude_model == "claude-3-sonnet-20240229"
    
    # Test validation errors
    with pytest.raises(ValidationError):
        InvestigateSingleRepoRequest(
            repo_name="",  # Empty repo name should fail
            repo_url="https://github.com/test/repo"
        )
    
    with pytest.raises(ValidationError):
        InvestigateSingleRepoRequest(
            repo_name="test-repo",
            repo_url="invalid-url"  # Invalid URL should fail
        )
    
    print("✅ Workflow request model validates inputs properly")


def test_workflow_investigation_decision_structure():
    """
    Test that investigation decisions have the expected structure.
    This tests BEHAVIOR: decisions contain the necessary information.
    """
    from models.investigation import InvestigationDecision
    
    # Test that InvestigationDecision can represent different scenarios
    
    # Test "needs investigation" decision
    needs_investigation = InvestigationDecision(
        needs_investigation=True,
        reason="New commits detected",
        latest_commit="abc123def456",
        branch_name="main"
    )
    assert needs_investigation.needs_investigation is True
    assert "commits" in needs_investigation.reason.lower()
    
    # Test "no investigation needed" decision  
    no_investigation = InvestigationDecision(
        needs_investigation=False,
        reason="No changes since last investigation",
        latest_commit="abc123def456",
        branch_name="main"
    )
    assert no_investigation.needs_investigation is False
    assert "no changes" in no_investigation.reason.lower()
    
    print("✅ Investigation decisions have proper structure")


def test_workflow_result_model_structure():
    """
    Test that workflow result models have the expected structure.
    This tests BEHAVIOR: results contain all necessary information.
    """
    from models import InvestigateSingleRepoResult
    
    # Test successful result
    success_result = InvestigateSingleRepoResult(
        status="success",
        repo_name="test-repo",
        repo_url="https://github.com/test/repo",
        repo_type="backend",
        arch_file_path="/tmp/arch.md",
        analysis_steps=5,
        prompt_versions={"hl_overview": "2", "dependencies": "1"},
        latest_commit="abc123def456",
        branch_name="main",
        cached=False,
        reason="Full investigation completed",
        message="Repository test-repo investigation completed successfully"
    )
    
    assert success_result.status == "success"
    assert success_result.analysis_steps == 5
    assert success_result.cached == False
    assert len(success_result.prompt_versions) == 2
    
    # Test skipped result
    skipped_result = InvestigateSingleRepoResult(
        status="skipped",
        repo_name="test-repo",
        repo_url="https://github.com/test/repo",
        repo_type="backend",
        latest_commit="abc123def456",
        branch_name="main",
        cached=True,
        reason="No changes since last investigation",
        message="Repository test-repo skipped: No changes since last investigation"
    )
    
    assert skipped_result.status == "skipped"
    assert skipped_result.cached == True
    assert "no changes" in skipped_result.reason.lower()
    
    print("✅ Workflow result models have proper structure")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v'])

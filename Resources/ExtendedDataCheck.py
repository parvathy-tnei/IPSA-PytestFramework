# import uuid

# from Logger import debug, info, error

# COMPONENT_GETTERS = (
#     "GetBusbars",
#     "GetBranches",
#     "GetTransformers",
#     "GetLoads",
#     "GetGenerators",
#     "GetInductionMachines",
#     "GetSynchronousMachines",
#     "GetShunts",
#     "GetFilters",
# )


# def run_extended_data_check(net):
#     """
#     Verify that extended-data fields can be added and deleted.

#     Tests one representative component from each supported,
#     non-empty component collection.

#     Existing extended-data fields are not modified.
#     Returns a list containing the successful operations.
#     """
#     debug("Starting Extended Data Check automation")

#     results = []

#     try:
#         for getter_name in COMPONENT_GETTERS:
#             getter = getattr(net, getter_name, None)

#             if not callable(getter):
#                 debug(f"{getter_name} is not available; skipping")
#                 continue

#             components = getter() or {}

#             if not components:
#                 debug(f"{getter_name} contains no components; skipping")
#                 continue

#             component_name, component = next(iter(components.items()))

#             # Use a unique name to avoid existing fields.
#             field_name = f"extended_{uuid.uuid4().hex}"

#             info(
#                 f"Testing extended data on "
#                 f"{getter_name}: {component_name}"
#             )

#             field_created = False

#             try:
#                 # Add a temporary Double field.
#                 add_result = component.AddDataExtension(
#                     field_name,
#                     123.45,
#                 )

#                 extension_names = component.GetExtensionNames()
#                 field_created = field_name in extension_names.values()

#                 if not field_created:
#                     raise AssertionError(
#                         f"Add failed: '{field_name}' was not found "
#                         f"after AddDataExtension(). "
#                         f"API return value: {add_result}"
#                     )

#                 info(
#                     f"ADD PASSED: '{field_name}' on "
#                     f"{component_name}"
#                 )

#                 # Delete the temporary field.
#                 delete_result = component.DeleteDataExtensionField(
#                     field_name
#                 )

#                 extension_names = component.GetExtensionNames()
#                 field_remaining = (
#                     field_name in extension_names.values()
#                 )

#                 if not delete_result or field_remaining:
#                     raise AssertionError(
#                         f"DELETE FAILED for '{field_name}' on "
#                         f"{component_name}. "
#                         f"API return value: {delete_result}; "
#                         f"field still present: {field_remaining}"
#                     )

#                 # Field successfully deleted.
#                 field_created = False

#                 info(
#                     f"DELETE PASSED: '{field_name}' on "
#                     f"{component_name}"
#                 )

#                 results.append({
#                     "Component Type": getter_name,
#                     "Component": component_name,
#                     "Field": field_name,
#                     "Add": "PASS",
#                     "Delete": "PASS",
#                 })

#             finally:
#                 # Best-effort cleanup if an assertion or API call fails.
#                 if field_created:
#                     try:
#                         current_names = component.GetExtensionNames()

#                         if field_name in current_names.values():
#                             component.DeleteDataExtensionField(
#                                 field_name
#                             )

#                             info(
#                                 f"Cleanup attempted for '{field_name}'"
#                             )

#                     except Exception as cleanup_exc:
#                         error(
#                             f"Cleanup failed for '{field_name}': "
#                             f"{cleanup_exc}"
#                         )

#         if not results:
#             raise RuntimeError(
#                 "No components were available for Extended Data testing."
#             )

#         info(
#             f"Extended Data Check completed: "
#             f"{len(results)} component collections passed."
#         )

#         return results

#     except Exception as exc:
#         error(f"Extended Data Check failed: {exc}")
#         raise




import uuid

from Logger import debug, info, error


COMPONENT_GETTERS = (
    "GetBusbars",
    "GetBranches",
    "GetTransformers",
    "GetLoads",
    "GetGenerators",
    "GetInductionMachines",
    "GetSynchronousMachines",
    "GetShunts",
    "GetFilters",
)


# Scalar fields: field name, initial value.
SCALAR_TESTS = (
    ("Double", 123.45),
    ("Integer", 123),
    ("Boolean", True),
    ("String", "ExtendedDataTest"),
)


# List fields: field name, creation method, append method,
# size method, read method, expected values.
LIST_TESTS = (
    (
        "ListOfIntegers",
        "AddListIntDataExtension",
        "PushBackListIntExtensionValue",
        "GetListIntSize",
        "GetListIntExtensionValue",
        [10, 20],
    ),
    (
        "ListOfDoubles",
        "AddListDblDataExtension",
        "PushBackListDblExtensionValue",
        "GetListDblSize",
        "GetListDblExtensionValue",
        [12.5, 24.75],
    ),
    (
        "ListOfStrings",
        "AddListStrDataExtension",
        "PushBackListStrExtensionValue",
        "GetListStrSize",
        "GetListStrExtensionValue",
        ["First", "Second"],
    ),
)


def _get_extension_names(component):
    """Return the component's extension field index-to-name mapping."""
    return component.GetExtensionNames() or {}


def _find_field_index(component, field_name):
    """Return the field index if the field exists, otherwise None."""
    for index, name in _get_extension_names(component).items():
        if name == field_name:
            return index
    return None


def _delete_test_field(component, field_name):
    """
    Delete only a field created by this test.

    A field definition is shared by components of the same type.
    Do not delete it if more than one component has non-default data.
    """
    field_index = _find_field_index(component, field_name)

    if field_index is None:
        return True

    count = component.NonDefaultExtensionInstanceCount(field_index)

    info(
        f"Cleanup check: '{field_name}' has "
        f"{count} non-default component instance(s)."
    )

    if count > 1:
        raise RuntimeError(
            f"Safety check prevented deletion of '{field_name}': "
            f"{count} components have non-default data."
        )

    deleted = component.DeleteDataExtensionField(field_index)

    if not deleted:
        raise AssertionError(
            f"DeleteDataExtensionField returned False for '{field_name}'."
        )

    if _find_field_index(component, field_name) is not None:
        raise AssertionError(
            f"Field '{field_name}' still exists after deletion."
        )

    return True


def _test_scalar(component, component_name, getter_name,
                 type_name, value, suffix):
    """Test creation and deletion of one scalar field."""
    field_name = f"pytest_ext_{type_name}_{suffix}"
    field_created = False
    result = {
        "Component Type": getter_name,
        "Component": component_name,
        "Data Type": type_name,
        "Field": field_name,
        "Add": "FAIL",
        "Verify": "FAIL",
        "Delete": "NOT RUN",
    }

    try:
        info(f"Adding {type_name} field '{field_name}'")

        # AddDataExtension overloads support bool, int, float and str.
        add_result = component.AddDataExtension(field_name, value)

        field_index = _find_field_index(component, field_name)
        field_created = field_index is not None

        if not field_created:
            raise AssertionError(
                f"'{field_name}' was not found after AddDataExtension(). "
                f"API return value: {add_result}"
            )

        result["Add"] = "PASS"
        result["Verify"] = "PASS"

        info(
            f"ADD/VERIFY PASSED: {type_name} field '{field_name}', "
            f"index={field_index}"
        )

        # Scalar value read-back is not included here because the
        # getter APIs for scalar Extended Data have not been verified.
        result["Verification Detail"] = "Field registration verified"

    except Exception as exc:
        result["Error"] = str(exc)
        error(f"{type_name} test failed: {exc}")

    finally:
        if field_created:
            try:
                _delete_test_field(component, field_name)
                result["Delete"] = "PASS"
                info(f"DELETE PASSED: '{field_name}'")
            except Exception as cleanup_exc:
                result["Delete"] = "FAIL"
                result["Cleanup Error"] = str(cleanup_exc)
                error(
                    f"Cleanup failed for '{field_name}': "
                    f"{cleanup_exc}"
                )

    return result


def _test_list(component, component_name, getter_name, test, suffix):
    """Create, populate, verify and delete one list field."""
    (
        type_name,
        add_method_name,
        push_method_name,
        size_method_name,
        get_method_name,
        expected_values,
    ) = test

    field_name = f"pytest_ext_{type_name}_{suffix}"
    field_created = False

    result = {
        "Component Type": getter_name,
        "Component": component_name,
        "Data Type": type_name,
        "Field": field_name,
        "Add": "FAIL",
        "Verify": "FAIL",
        "Delete": "NOT RUN",
    }

    try:
        info(f"Adding {type_name} field '{field_name}'")

        add_method = getattr(component, add_method_name)
        field_index = add_method(field_name)

        field_created = (
            _find_field_index(component, field_name) is not None
        )

        if not field_created:
            raise AssertionError(
                f"'{field_name}' was not found after creation. "
                f"API return value: {field_index}"
            )

        result["Add"] = "PASS"

        # Append test values using the verified PushBack methods.
        push_method = getattr(component, push_method_name)

        for value in expected_values:
            append_result = push_method(field_index, value)

            if not append_result:
                raise AssertionError(
                    f"{push_method_name} returned False for {value!r}."
                )

        size_method = getattr(component, size_method_name)
        get_method = getattr(component, get_method_name)

        actual_size = size_method(field_index)
        actual_values = [
            get_method(field_index, index)
            for index in range(actual_size)
        ]

        if actual_size != len(expected_values):
            raise AssertionError(
                f"Expected {len(expected_values)} elements, "
                f"got {actual_size}."
            )

        if actual_values != expected_values:
            raise AssertionError(
                f"List values differ. Expected {expected_values!r}; "
                f"received {actual_values!r}."
            )

        result["Verify"] = "PASS"
        result["Expected Values"] = expected_values
        result["Actual Values"] = actual_values

        info(
            f"ADD/VERIFY PASSED: {type_name}; "
            f"values={actual_values!r}"
        )

    except Exception as exc:
        result["Error"] = str(exc)
        error(f"{type_name} test failed: {exc}")

    finally:
        if field_created:
            try:
                _delete_test_field(component, field_name)
                result["Delete"] = "PASS"
                info(f"DELETE PASSED: '{field_name}'")
            except Exception as cleanup_exc:
                result["Delete"] = "FAIL"
                result["Cleanup Error"] = str(cleanup_exc)
                error(
                    f"Cleanup failed for '{field_name}': "
                    f"{cleanup_exc}"
                )

    return result


def run_extended_data_check(net):
    """
    Test all seven IPSA Extended Data types.

    Tests one representative component from every supported,
    non-empty component collection.

    Scalar fields:
        Verify field creation and deletion.

    List fields:
        Verify creation, appending, list size, read-back values
        and deletion.

    Existing fields are not intentionally modified. Unique test
    names are used, and cleanup checks the non-default instance
    count before deleting each field.

    Returns:
        A list of per-type test result dictionaries.

    Raises:
        RuntimeError if no tests could be executed or any test fails.
    """
    debug("Starting Extended Data Check automation")

    results = []
    failures = []

    try:
        for getter_name in COMPONENT_GETTERS:
            getter = getattr(net, getter_name, None)

            if not callable(getter):
                debug(f"{getter_name} is not available; skipping")
                continue

            components = getter() or {}

            if not components:
                debug(
                    f"{getter_name} contains no components; skipping"
                )
                continue

            component_name, component = next(iter(components.items()))

            info(
                f"Testing Extended Data on "
                f"{getter_name}: {component_name}"
            )

            # Use one suffix per component, with distinct field names
            # for all seven data types.
            suffix = uuid.uuid4().hex

            for type_name, value in SCALAR_TESTS:
                result = _test_scalar(
                    component,
                    component_name,
                    getter_name,
                    type_name,
                    value,
                    suffix,
                )
                results.append(result)

                if (
                    result["Add"] != "PASS"
                    or result["Verify"] != "PASS"
                    or result["Delete"] != "PASS"
                ):
                    failures.append(result)

            for test in LIST_TESTS:
                result = _test_list(
                    component,
                    component_name,
                    getter_name,
                    test,
                    suffix,
                )
                results.append(result)

                if (
                    result["Add"] != "PASS"
                    or result["Verify"] != "PASS"
                    or result["Delete"] != "PASS"
                ):
                    failures.append(result)

        if not results:
            raise RuntimeError(
                "No components were available for Extended Data testing."
            )

        info(
            f"Extended Data Check finished: "
            f"{len(results) - len(failures)}/{len(results)} "
            f"type tests passed."
        )

        if failures:
            details = "; ".join(
                f"{item['Component Type']} / {item['Data Type']}: "
                f"Add={item['Add']}, Verify={item['Verify']}, "
                f"Delete={item['Delete']}"
                for item in failures
            )

            raise RuntimeError(
                f"Extended Data Check failed for "
                f"{len(failures)} test(s). {details}"
            )

        return results

    except Exception as exc:
        error(f"Extended Data Check failed: {exc}")
        raise


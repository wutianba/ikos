#*******************************************************************************
#
# Find IKOS core headers.
#
# Author: Maxime Arthaud
#
# Contact: ikos@lists.nasa.gov
#
# Notices:
#
# Copyright (c) 2011-2017 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Disclaimers:
#
# No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF
# ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS,
# ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# OR FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL BE
# ERROR FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED, WILL CONFORM TO
# THE SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, CONSTITUTE AN
# ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS,
# RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS
# RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY
# DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE,
# IF PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."
#
# Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST
# THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL
# AS ANY PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS
# IN ANY LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH
# USE, INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM,
# RECIPIENT'S USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD
# HARMLESS THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS,
# AS WELL AS ANY PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.
# RECIPIENT'S SOLE REMEDY FOR ANY SUCH MATTER SHALL BE THE IMMEDIATE,
# UNILATERAL TERMINATION OF THIS AGREEMENT.
#
#*****************************************************************************/

if (NOT IKOS_FOUND)
  set(IKOS_INCLUDE_SEARCH_DIRS "")

  # use IKOS_ROOT as a hint
  set(IKOS_ROOT "" CACHE PATH "Path to ikos install directory.")

  if (IKOS_ROOT)
    list(APPEND IKOS_INCLUDE_SEARCH_DIRS "${IKOS_ROOT}/include")
  endif()

  # use ikos-config --includedir as a hint
  find_program(IKOS_CONFIG_EXECUTABLE CACHE NAMES ikos-config DOC "ikos-config executable")

  if (IKOS_CONFIG_EXECUTABLE)
    execute_process(
      COMMAND ${IKOS_CONFIG_EXECUTABLE} --includedir
      OUTPUT_VARIABLE IKOS_CONFIG_INCLUDE_DIR
      OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    list(APPEND IKOS_INCLUDE_SEARCH_DIRS "${IKOS_CONFIG_INCLUDE_DIR}")
  endif()

  find_path(IKOS_INCLUDE_DIR
    NAMES ikos/iterators/fwd_fixpoint_iterators.hpp
    NAMES ikos/domains/intervals.hpp
    HINTS ${IKOS_INCLUDE_SEARCH_DIRS}
  )

  mark_as_advanced(IKOS_INCLUDE_DIR)

  include(FindPackageHandleStandardArgs)
  find_package_handle_standard_args(IKOS
    REQUIRED_VARS IKOS_INCLUDE_DIR
    FAIL_MESSAGE "Could NOT find IKOS. Please provide -DIKOS_ROOT=<ikos-directory>")
endif()

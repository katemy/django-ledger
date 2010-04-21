# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: pdf_latex.py 310 2008-10-02 17:24:23Z copelco $
# ----------------------------------------------------------------------------
#
#    Copyright (C) 2008 Caktus Consulting Group, LLC
#
#    This file is part of minibooks.
#
#    minibooks is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of 
#    the License, or (at your option) any later version.
#    
#    minibooks is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    
#    You should have received a copy of the GNU Affero General Public License
#    along with minibooks.  If not, see <http://www.gnu.org/licenses/>.
#


import os
import shutil
import tempfile
import logging
import subprocess

from django.template.loader import render_to_string
from django.conf import settings


def render_to_pdf_string(path, context):
    """
    Render file (path) to a PDF and return it
    
     * create temporary file
     * write tex to it
     * use Popen to run pdflatex
     * open resulting PDF file and return it
     * cleanup temporary files
    
     -- use file i/o rather than pipes because
        I can't get them to work with batchmode
    """
    
    # create temporary .tex file
    directory_path = tempfile.mkdtemp()
    file_number, file_path = tempfile.mkstemp(
        settings.TEX_EXTENSION,
        '',
        directory_path,
    )
    
    # render template and save to .tex file
    f = os.fdopen(file_number, 'w')
    string = render_to_string(path, context)
    f.write(string.encode("utf-8"))
    #f.write(string.encode("iso-8859-1"))
    f.close()
    
    # run pdflatex on temporary .tex file
    os.chdir(directory_path)
    p = subprocess.Popen(
        '%s %s' % (settings.LATEX_CMD, file_path),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    (child_stdin, child_stdout_and_stderr) = (p.stdin, p.stdout)
    pdflatex_output = child_stdout_and_stderr.read()
    if (pdflatex_output.find('Fatal') > 0):
        raise IOError(pdflatex_output)
    os.waitpid(p.pid, 0)
    
    # open resulting PDF and return it
    pdf_file = file_path.replace(
        settings.TEX_EXTENSION,
        settings.PDF_EXTENSION,
    )
    f = open(pdf_file, 'r')
    output = f.read()
    f.close()
    
    shutil.rmtree(directory_path)
    return output

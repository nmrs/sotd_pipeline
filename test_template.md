# Test Report

## Overview
This is a test template to verify the new universal table generator works correctly.

## Razors Table
{{tables.razors}}

## Top 5 Razors
{{tables.razors|ranks:5}}

## First 3 Razors
{{tables.razors|rows:3}}

## Soap Makers Table
{{tables.soap-makers}}

## Top 10 Soap Makers
{{tables.soap-makers|ranks:10}}

## Error Test
{{tables.unknown-table}}

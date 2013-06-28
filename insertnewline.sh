#!/bin/bash

sed 's/\/art>/\/art>\'$'\n/g' | sed 's/\/>/\/>\'$'\n/g' 


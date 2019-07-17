# tapflap-coding.R                                
# functions for sorting tap/flap coding results into dataframe.
# Jennifer Kuo (July 2019)

## load packages
require(tidyverse)
require(knitr)

### function for getting all coding results and organizing them into one summary dataframe
## basic command:
## make.code.file()
make.code.file <- function(expdirname, file_a1,file_a2,file_b1,file_b2){
        a1 <- read.delim(file_a1,header = T,sep = "\t")
        a2 <- read.delim(file_a2,header = T,sep = "\t")
        b1 <- read.delim(file_b1,header = T,sep = "\t") 
        b2 <- read.delim(file_b2,header = T,sep = "\t") 
        
        a_comb <- left_join(a1,a2,by=c("acq" = "acq")) %>% 
                mutate(agree = label.x==label.y)
        a_agreement <- round(100 * (table(a_comb$agree)/nrow(a_comb))[2])
        message(paste0("Agreement rate between ", a1$ann[1], 
                     " and ", a2$ann[1], " is ", a_agreement, "%."))
        
        b_comb <- left_join(b1,b2,by=c("acq" = "acq")) %>% 
                mutate(agree = label.x==label.y)
        b_agreement <- round(100 * (table(b_comb$agree)/nrow(b_comb))[2])
        message(paste0("Agreement rate between ", b1$ann[1], 
                     " and ", b2$ann[1], " is ", b_agreement, "%. \n \n \n"))
        options(warn=-1)
        all <- bind_rows(a_comb,b_comb)
        options(warn=0)
        write.csv(all,paste0(expdirname,"_code_all.csv"),row.names = FALSE)
        
        all_disagree <- all %>% 
                filter(!agree) %>% 
                mutate(err_type = paste0(label.x,"_vs_",label.y),
                       err_type = as.factor(err_type)) 
        write.csv(all_disagree,paste0(expdirname,"_code_disagree.csv"),row.names = FALSE)
        
        a_disagree <- all_disagree %>% 
                filter(ann.x == a1$ann[1])
        message(paste0(a1$ann[1], " vs.", a2$ann[1],":"))
        print(kable(table(a_disagree$label.x,a_disagree$label.y)))
        
        message("\n \n \n")
        b_disagree <- all_disagree %>% 
                filter(ann.x == b1$ann[1])
        message(paste0(b1$ann[1], "vs.", b2$ann[1],":"))
        print(kable(table(b_disagree$label.x,b_disagree$label.y)))
        
}

add.recoding <- function(codefile, recoding){
        all <- read.csv(codefile)
}

# 
# a1 <- read.delim("FL02_a_JA.txt",header = T,sep = "\t")
# a2 <- read.delim("FL02_a_MF.txt",header = T,sep = "\t")
# b1 <- read.delim("FL02_b_JJ.txt",header = T,sep = "\t") 
# b2 <- read.delim("FL02_b_JW.txt",header = T,sep = "\t") 
# 
# 
# a_comb <- left_join(a1,a2,by=c("acq" = "acq")) %>% 
#      mutate(agree = label.x==label.y)
# 
# b_comb <- left_join(b1,b2,by=c("acq" = "acq")) %>% 
#         mutate(agree = label.x==label.y)
# table(b_comb$agree)
# 
# all <- bind_rows(a_comb,b_comb)
# write.csv(all,"FL02_code_all.csv",row.names = FALSE)
# 
# 
# 
# 
# 
# all_disagree <- all %>% 
#         filter(!agree) %>% 
#         mutate(err_type = paste0(label.x,"_vs_",label.y),
#                err_type = as.factor(err_type)) 
# 
# table(all_disagree$err_type)
# table(all_disagree$label.x,all_disagree$label.y)
# # down_flap high_tap low_tap up_flap
# # down_flap         0       15      13       0
# # high_tap         69        0      21      27
# # low_tap          28       13       0      45
# # up_flap           9        0       0       0
# 
# 
# a_disagree <- all_disagree %>% 
#         filter(ann.x == "ja")
# b_disagree <- all_disagree %>% 
#         filter(ann.x !="ja")
# 
# table(a_disagree$label.x,a_disagree$label.y)
#                 # down_flap high_tap low_tap up_flap
# # down_flap         0       15       0       0
# # high_tap         29        0      13      27
# # low_tap          18       11       0       6
# # up_flap           1        0       0       0
# 
# table(b_disagree$label.x,b_disagree$label.y)
#                 # down_flap high_tap low_tap up_flap
# # down_flap         0        0      13       0
# # high_tap         40        0       8       0
# # low_tap          10        2       0      39
# # up_flap           8        0       0       0
# 
# 
# all_disagree <- arrange(all_disagree, err_type)
# write.csv(all_disagree,"FL02_all_disag.csv")
# 
# 
# 
# 
# 
# #################
# disagree <- all %>% 
#      filter(agree == FALSE) %>% 
#      mutate(err.type = paste0(label.x,'/',label.y)) %>% 
#      group_by(err.type) %>% 
#      mutate(count = n()) %>% 
#      ungroup() %>% 
#      arrange(desc(count))
# 
# write.csv(all,"FL01_code_JakeJoy.csv",row.names = FALSE)
# write.csv(disagree,"FL01_code_JakeJoy_disagree.csv",row.names = FALSE)
# table(disagree$label.x,disagree$label.y)
# 
# 
# jinyoung <- read.csv("FL01_jinyoung.csv",header = T)
# noah <- read.csv("FL01_noah.csv",header = T) %>% 
#         select(acq,ann,label) 
# all <- left_join(jinyoung,noah,by=c("acq" = "acq")) %>% 
#         mutate(agree = label.x==label.y)
# 
# table(all$agree)
# disagree <- all %>% 
#         filter(agree == FALSE) %>% 
#         mutate(err.type = paste0(label.x,'/',label.y)) %>% 
#         group_by(err.type) %>% 
#         mutate(count = n()) %>% 
#         ungroup() %>% 
#         arrange(desc(count))
# 
# write.csv(all,"FL01_code_JinyoungNoah.csv",row.names = FALSE)
# write.csv(disagree,"FL01_code_JinyoungNoah_disagree.csv",row.names = FALSE)
# table(disagree$label.x,disagree$label.y)
# 
# 
# 
# 
# # COMBINING CODING ERRORs -------------------------------------------------
# rm(list = ls())
# setwd("~/tapflap/coding-results/FL02_codes")
# library(tidyverse)
# 
# pt1 <- read.csv("FL01_code_JinyoungNoah.csv")
# pt2 <- read.csv("FL01_code_JakeJoy.csv")
# 
# all <- bind_rows(pt1,pt2) %>% 
#         mutate(agree = label.x==label.y)
#        # mutate(err_type = paste0(label.x,'/',label.y)) %>% 
#        # mutate(err_type = gsub("/","_vs_",err_type)) 
# 
# write.csv(all,"FL01_code_all.csv",row.names = FALSE)
# 
# 
# pt1_dis <- read.csv("FL01_code_JinyoungNoah_disagree.csv")
# pt2_dis <- read.csv("FL01_code_JakeJoy_disagree.csv")
# all <- bind_rows(pt1_dis,pt2_dis) %>% 
#         mutate(err_type = paste0(label.x,'/',label.y)) %>% 
#         mutate(err_type = gsub("/","_vs_",err_type)) 
# summary <- all %>% 
#         group_by(err_type) %>% 
#         group_split()
# for (subframe in summary){
#         err_type <- subframe$err_type[1]
#         #coders <- tolower(paste0(subframe$ann.x[1],subframe$ann.y[2]))
#         write.csv(subframe,paste0(err_type,".csv"),row.names = FALSE)
# }
# 
# 
# 
# 
# # UNSORTED FILES BY TYPE --------------------------------------------------
# setwd("~/tapflap/coding-results/FL02_codes")
# all_FLO2 <- read.csv("~/tapflap/coding-results/FL02_codes/FL02_code_all.csv")
# library(tidyverse)
# dirs <- list.dirs()
# dirs <- gsub("[.]","",dirs)
# dirs <- gsub("[/]inClass[/]","",dirs)
# 
# unsorted <- all_FLO1 %>% 
#         filter((acq %in% dirs)) %>% 
#         select(acq,stim,before,after,ann.x,ann.y,label.x,label.y)
# write.csv(unsorted,"error-types.csv")
# colnames(unsorted)
# 
# inclass <- read.delim("recode-inclass-FL01/annotations_inclass_FL01.txt",sep="\t")
# jake <- read.delim("recode_ja.txt",sep="\t")
# joy <- read.delim("recode_jw.txt",sep="\t")
# jinyoung <- read.delim("recode_jj.txt",sep="\t")
# colnames(jinyoung) <- c("acq","stim","before","after","voi","ann3","label3")
# colnames(jake) <- c("acq","stim","before","after","voi","ann3","label3")
# colnames(joy) <- c("acq","stim","before","after","voi","ann3","label3")
# 
# colnames(inclass) <- c("acq","stim","before","after","voi","ann3","label3")
# 
# recodes <- rbind(jinyoung,jake,joy,inclass)
# 
# all_FLO1 <- all_FLO1 %>% 
#         left_join(recodes)
# all_FLO1 <- all_FLO1 %>% 
#         mutate(final.label = NA,
#                final.label = ifelse(label.x==label3,as.character(label.x),final.label),
#                final.label = ifelse(label.y==label3,as.character(label.y),final.label),
#                final.label = ifelse(!(is.na(label3) & is.na(final.label)),as.character(label3),final.label),
#                final.label = ifelse(agree, as.character(label.x),final.label))
# 
# write.csv(all_FLO1, "FL01_code_all2.csv",row.names = F)

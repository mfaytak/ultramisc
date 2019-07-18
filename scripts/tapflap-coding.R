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


